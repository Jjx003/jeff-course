# Tips & Notes

## Concatenating two tuples

```cpp
Tuple ConcatTuples(const Tuple& left, const Tuple& right) {
    Tuple result;
    auto& ld = left.Data();
    auto& rd = right.Data();
    result.data_.insert(result.data_.end(), ld.begin(), ld.end());
    result.data_.insert(result.data_.end(), rd.begin(), rd.end());
    return result;
}
```

You'll need to make `data_` accessible (add a getter or make the function a friend).

## Combined schema for printing

```cpp
Schema CombineSchemas(const Schema& l, const Schema& r) {
    // Re-create with all columns from l then all from r
    std::vector<std::pair<std::string, TypeId>> cols;
    for (size_t i = 0; i < l.NumColumns(); ++i)
        cols.push_back({l.GetColumn(i).name, l.GetColumn(i).type});
    for (size_t i = 0; i < r.NumColumns(); ++i)
        cols.push_back({r.GetColumn(i).name, r.GetColumn(i).type});
    return Schema(cols.begin(), cols.end());
}
```

Note: you'll need to add a range constructor to `Schema` or compute the combined schema manually.

## NLJ state machine

```cpp
void Init() override {
    // Materialise left
    left_->Init();
    while (Tuple* t = left_->Next()) left_tuples_.push_back(*t);
    left_->Close();
    left_idx_  = 0;
    right_->Init();
    cur_right_ = right_->Next();
}

Tuple* Next() override {
    while (left_idx_ < left_tuples_.size()) {
        while (cur_right_ != nullptr) {
            Tuple* r = cur_right_;
            cur_right_ = right_->Next();
            if (join_pred_(left_tuples_[left_idx_], *r)) {
                current_ = concat(left_tuples_[left_idx_], *r);
                return &current_;
            }
        }
        ++left_idx_;
        right_->Init();
        cur_right_ = right_->Next();
    }
    return nullptr;
}
```

Wait — there's a subtlety: after calling `right_->Next()` to advance past `r`, the pointer `r` may be invalidated (since the executor stores one tuple internally). Copy `*r` before advancing:

```cpp
Tuple r_copy = *cur_right_;
cur_right_ = right_->Next();
if (join_pred_(left_tuples_[left_idx_], r_copy)) { ... }
```

## Hash join probe state

Track which bucket and which position within the bucket you're currently emitting from:

```cpp
std::vector<Tuple>* cur_bucket_{nullptr};
size_t              bucket_idx_{0};
Tuple               cur_right_tuple_;
```

## Probing

```cpp
Tuple* Next() override {
    while (true) {
        // emit remaining matches from current bucket
        if (cur_bucket_ && bucket_idx_ < cur_bucket_->size()) {
            current_ = concat((*cur_bucket_)[bucket_idx_++], cur_right_tuple_);
            return &current_;
        }
        // advance right side
        Tuple* r = right_->Next();
        if (!r) return nullptr;
        cur_right_tuple_ = *r;
        int32_t key = right_key_fn_(cur_right_tuple_);
        auto it = hash_table_.find(key);
        if (it != hash_table_.end()) {
            cur_bucket_  = &it->second;
            bucket_idx_  = 0;
        } else {
            cur_bucket_ = nullptr;
        }
    }
}
```
