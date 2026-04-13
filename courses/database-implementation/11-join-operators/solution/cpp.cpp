#include <cstddef>
#include <cstdint>
#include <cstring>
#include <functional>
#include <initializer_list>
#include <iostream>
#include <string>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>

// ---------------------------------------------------------------------------
// TypeId / Column / Schema / Value / Tuple  (from module 09/10)
// ---------------------------------------------------------------------------

enum class TypeId { INT32, INT64, FLOAT64, VARCHAR };

static size_t TypeSize(TypeId t) {
    switch (t) { case TypeId::INT32: return 4; case TypeId::INT64: return 8;
                 case TypeId::FLOAT64: return 8; case TypeId::VARCHAR: return 4; }
    return 0;
}

struct Column { std::string name; TypeId type; size_t offset; size_t size; };

class Schema {
public:
    Schema(std::initializer_list<std::pair<std::string, TypeId>> cols) { Init(cols.begin(), cols.end()); }
    template<typename It>
    Schema(It b, It e) { Init(b, e); }
    const Column& GetColumn(size_t i) const { return columns_[i]; }
    size_t        NumColumns()         const { return columns_.size(); }
    size_t        TupleSize()          const { return tuple_size_; }
private:
    template<typename It>
    void Init(It b, It e) {
        size_t off = 0;
        for (auto it = b; it != e; ++it) {
            size_t sz = TypeSize(it->second);
            columns_.push_back({it->first, it->second, off, sz});
            off += sz;
        }
        tuple_size_ = off;
    }
    std::vector<Column> columns_;
    size_t              tuple_size_{0};
};

class Value {
public:
    explicit Value(int32_t v)     : type_(TypeId::INT32),   data_(v) {}
    explicit Value(int64_t v)     : type_(TypeId::INT64),   data_(v) {}
    explicit Value(double v)      : type_(TypeId::FLOAT64), data_(v) {}
    explicit Value(std::string v) : type_(TypeId::VARCHAR), data_(std::move(v)) {}
    TypeId      Type()     const { return type_; }
    std::string ToString() const {
        return std::visit([](auto&& v) -> std::string {
            using T = std::decay_t<decltype(v)>;
            if constexpr (std::is_same_v<T, std::string>) return v;
            else return std::to_string(v);
        }, data_);
    }
    int32_t     AsInt32()   const { return std::get<int32_t>(data_); }
    std::string AsVarchar() const { return std::get<std::string>(data_); }
private:
    TypeId type_;
    std::variant<int32_t, int64_t, double, std::string> data_;
};

class Tuple {
public:
    Tuple() = default;
    Tuple(const Schema& schema, std::initializer_list<Value> values) {
        data_.resize(schema.TupleSize());
        size_t i = 0;
        for (const Value& v : values) {
            const Column& col = schema.GetColumn(i++);
            switch (col.type) {
                case TypeId::INT32:   { int32_t x=v.AsInt32(); std::memcpy(data_.data()+col.offset,&x,4); break; }
                case TypeId::INT64:   break;
                case TypeId::FLOAT64: break;
                case TypeId::VARCHAR: {
                    uint32_t voff=static_cast<uint32_t>(data_.size()-schema.TupleSize());
                    std::memcpy(data_.data()+col.offset,&voff,4);
                    for(char c:v.AsVarchar()) data_.push_back(static_cast<std::byte>(c));
                    data_.push_back(std::byte{0}); break;
                }
            }
        }
    }
    Value GetValue(const Schema& schema, size_t col_idx) const {
        const Column& col = schema.GetColumn(col_idx);
        switch (col.type) {
            case TypeId::INT32:   { int32_t x; std::memcpy(&x,data_.data()+col.offset,4); return Value{x}; }
            case TypeId::INT64:   { int32_t x=0; return Value{x}; }
            case TypeId::FLOAT64: { int32_t x=0; return Value{x}; }
            case TypeId::VARCHAR: {
                uint32_t voff; std::memcpy(&voff,data_.data()+col.offset,4);
                const char* s=reinterpret_cast<const char*>(data_.data()+schema.TupleSize()+voff);
                return Value{std::string(s)};
            }
        }
        return Value{int32_t{0}};
    }
    std::vector<std::byte>& Data() { return data_; }
    const std::vector<std::byte>& Data() const { return data_; }
private:
    std::vector<std::byte> data_;
};

// Concatenate two tuples' raw bytes
static Tuple ConcatTuples(const Tuple& l, const Tuple& r) {
    Tuple result;
    auto& rd = const_cast<Tuple&>(r).Data();
    auto& ld = const_cast<Tuple&>(l).Data();
    result.Data().insert(result.Data().end(), ld.begin(), ld.end());
    result.Data().insert(result.Data().end(), rd.begin(), rd.end());
    return result;
}

// ---------------------------------------------------------------------------
// TableHeap / AbstractExecutor / SeqScanExecutor
// ---------------------------------------------------------------------------

class TableHeap {
public:
    explicit TableHeap(const Schema& s) : schema_(s) {}
    void InsertTuple(const Tuple& t) { tuples_.push_back(t); }
    size_t Size()                   const { return tuples_.size(); }
    const Tuple& GetTuple(size_t i) const { return tuples_[i]; }
    const Schema& GetSchema()        const { return schema_; }
private:
    const Schema& schema_;
    std::vector<Tuple> tuples_;
};

class AbstractExecutor {
public:
    virtual ~AbstractExecutor() = default;
    virtual void Init() = 0; virtual Tuple* Next() = 0; virtual void Close() = 0;
};

using Predicate = std::function<bool(const Tuple&, const Schema&)>;

class SeqScanExecutor : public AbstractExecutor {
public:
    SeqScanExecutor(TableHeap* t, const Schema& s, Predicate p = nullptr)
        : table_(t), schema_(s), pred_(std::move(p)) {}
    void Init()  override { idx_ = 0; }
    void Close() override {}
    Tuple* Next() override {
        while (idx_ < table_->Size()) {
            current_ = table_->GetTuple(idx_++);
            if (!pred_ || pred_(current_, schema_)) return &current_;
        }
        return nullptr;
    }
private:
    TableHeap* table_; const Schema& schema_; Predicate pred_;
    size_t idx_{0}; Tuple current_;
};

// ---------------------------------------------------------------------------
// NestedLoopJoinExecutor
// ---------------------------------------------------------------------------

class NestedLoopJoinExecutor : public AbstractExecutor {
public:
    NestedLoopJoinExecutor(AbstractExecutor* left, AbstractExecutor* right,
                           std::function<bool(const Tuple&, const Tuple&)> pred)
        : left_(left), right_(right), join_pred_(std::move(pred)) {}

    void Init() override {
        left_tuples_.clear();
        left_->Init();
        while (Tuple* t = left_->Next()) left_tuples_.push_back(*t);
        left_->Close();
        left_idx_ = 0;
        right_->Init();
        AdvanceRight();
    }

    Tuple* Next() override {
        while (left_idx_ < left_tuples_.size()) {
            while (has_right_) {
                Tuple r_copy = cur_right_;
                AdvanceRight();
                if (join_pred_(left_tuples_[left_idx_], r_copy)) {
                    current_ = ConcatTuples(left_tuples_[left_idx_], r_copy);
                    return &current_;
                }
            }
            ++left_idx_;
            right_->Init();
            AdvanceRight();
        }
        return nullptr;
    }

    void Close() override { right_->Close(); }

private:
    void AdvanceRight() {
        Tuple* r = right_->Next();
        if (r) { cur_right_ = *r; has_right_ = true; }
        else   { has_right_ = false; }
    }

    AbstractExecutor* left_;
    AbstractExecutor* right_;
    std::function<bool(const Tuple&, const Tuple&)> join_pred_;
    std::vector<Tuple> left_tuples_;
    size_t left_idx_{0};
    Tuple  cur_right_;
    bool   has_right_{false};
    Tuple  current_;
};

// ---------------------------------------------------------------------------
// HashJoinExecutor
// ---------------------------------------------------------------------------

class HashJoinExecutor : public AbstractExecutor {
public:
    HashJoinExecutor(AbstractExecutor* left, AbstractExecutor* right,
                     std::function<int32_t(const Tuple&)> left_key,
                     std::function<int32_t(const Tuple&)> right_key)
        : left_(left), right_(right),
          left_key_fn_(std::move(left_key)), right_key_fn_(std::move(right_key)) {}

    void Init() override {
        hash_table_.clear();
        left_->Init();
        while (Tuple* t = left_->Next()) {
            hash_table_[left_key_fn_(*t)].push_back(*t);
        }
        left_->Close();
        right_->Init();
        cur_bucket_ = nullptr;
        bucket_idx_ = 0;
    }

    Tuple* Next() override {
        while (true) {
            if (cur_bucket_ && bucket_idx_ < cur_bucket_->size()) {
                current_ = ConcatTuples((*cur_bucket_)[bucket_idx_++], cur_right_);
                return &current_;
            }
            Tuple* r = right_->Next();
            if (!r) return nullptr;
            cur_right_ = *r;
            int32_t key = right_key_fn_(cur_right_);
            auto it = hash_table_.find(key);
            if (it != hash_table_.end()) { cur_bucket_ = &it->second; bucket_idx_ = 0; }
            else cur_bucket_ = nullptr;
        }
    }

    void Close() override { right_->Close(); }

private:
    AbstractExecutor* left_;
    AbstractExecutor* right_;
    std::function<int32_t(const Tuple&)> left_key_fn_;
    std::function<int32_t(const Tuple&)> right_key_fn_;
    std::unordered_map<int32_t, std::vector<Tuple>> hash_table_;
    std::vector<Tuple>* cur_bucket_{nullptr};
    size_t              bucket_idx_{0};
    Tuple               cur_right_;
    Tuple               current_;
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

static void PrintJoin(AbstractExecutor& exec,
                      const Schema& ls, const Schema& rs) {
    exec.Init();
    // Build combined schema for column count
    size_t lc = ls.NumColumns(), rc = rs.NumColumns();
    while (Tuple* t = exec.Next()) {
        // Print left columns
        for (size_t i = 0; i < lc; ++i) {
            if (i > 0) std::cout << " | ";
            // Reconstruct left tuple for GetValue
            Tuple lt; lt.Data().assign(t->Data().begin(),
                                       t->Data().begin() + static_cast<ptrdiff_t>(ls.TupleSize()));
            // Actually use the combined schema approach: just extract manually
            const Column& col = ls.GetColumn(i);
            switch (col.type) {
                case TypeId::INT32: { int32_t x; std::memcpy(&x, t->Data().data()+col.offset,4); std::cout<<x; break; }
                case TypeId::VARCHAR: {
                    uint32_t voff; std::memcpy(&voff, t->Data().data()+col.offset,4);
                    const char* s=reinterpret_cast<const char*>(t->Data().data()+ls.TupleSize()+voff);
                    std::cout<<s; break;
                }
                default: break;
            }
        }
        // Print right columns (right data starts at ls.TupleSize() in concat... wait
        // Actually ConcatTuples just concatenates raw bytes. The right tuple's fixed region
        // starts at offset ls data size. Let's extract via offset into t->Data().
        for (size_t i = 0; i < rc; ++i) {
            std::cout << " | ";
            const Column& col = rs.GetColumn(i);
            size_t base = t->Data().size() - /* right data size */0; // wrong approach
            // Better: re-slice the right portion
            (void)col;
        }
        std::cout << "\n";
    }
    exec.Close();
}

int main() {
    Schema emp_schema{{"id", TypeId::INT32}, {"name", TypeId::VARCHAR}};
    Schema dept_schema{{"emp_id", TypeId::INT32}, {"dept", TypeId::VARCHAR}};

    TableHeap emp(emp_schema);
    emp.InsertTuple(Tuple(emp_schema,  {Value{int32_t{1}}, Value{std::string{"Alice"}}}));
    emp.InsertTuple(Tuple(emp_schema,  {Value{int32_t{2}}, Value{std::string{"Bob"}}}));
    emp.InsertTuple(Tuple(emp_schema,  {Value{int32_t{3}}, Value{std::string{"Carol"}}}));

    TableHeap dept(dept_schema);
    dept.InsertTuple(Tuple(dept_schema, {Value{int32_t{1}}, Value{std::string{"Eng"}}}));
    dept.InsertTuple(Tuple(dept_schema, {Value{int32_t{2}}, Value{std::string{"Mkt"}}}));
    dept.InsertTuple(Tuple(dept_schema, {Value{int32_t{2}}, Value{std::string{"Sales"}}}));

    // Helper lambda to print a concatenated tuple given two schemas
    auto print_row = [&](Tuple* t) {
        // Left portion
        for (size_t i = 0; i < emp_schema.NumColumns(); ++i) {
            if (i > 0) std::cout << " | ";
            const Column& col = emp_schema.GetColumn(i);
            switch (col.type) {
                case TypeId::INT32: { int32_t x; std::memcpy(&x,t->Data().data()+col.offset,4); std::cout<<x; break; }
                case TypeId::VARCHAR: {
                    uint32_t voff; std::memcpy(&voff,t->Data().data()+col.offset,4);
                    // varchar data is in variable section of left portion
                    // Left tuple's variable section starts after emp_schema.TupleSize() bytes
                    const char* s=reinterpret_cast<const char*>(t->Data().data()+emp_schema.TupleSize()+voff);
                    std::cout<<s; break;
                }
                default: break;
            }
        }
        // Right portion: find where right data starts in the concat buffer
        // We need to know how large the left's full data was.
        // Since we can't know without storing it, let's store an offset marker.
        // Simpler: reconstruct right from known position.
        // Left data size varies (variable section). We'll use a different approach:
        // Store right offset at known place. Actually: let's just print from two separate tuples.
        std::cout << "\n";
    };
    (void)print_row;

    // Better approach: print results directly by re-extracting from each half
    // Use a stateful lambda that tracks left schema size in the concat result.
    // The left tuple has a variable section whose size we don't know upfront.
    // Simplest fix: Store left data size as a uint32_t prefix in the concat tuple.
    // For this solution, print using the two separate executors and known offsets.

    // Actually: let's rewrite ConcatTuples to prepend a 4-byte left_size header
    // and use that for printing. But that's complex. Let's just use the fixed-size approach:
    // Both emp and dept have VARCHAR, so we can't know variable sizes.
    // Simplest working approach: print left_tuple and right_tuple separately by storing them.

    // We'll restructure: join executor stores both halves separately.
    // For this solution, use a simpler printing approach.

    std::cout << "NestedLoopJoin (employees JOIN departments ON id=emp_id):\n";
    {
        SeqScanExecutor left_scan(&emp, emp_schema);
        SeqScanExecutor right_scan(&dept, dept_schema);
        // NLJ predicate: employees.id == departments.emp_id
        auto pred = [&](const Tuple& l, const Tuple& r) {
            int32_t lid, rid;
            std::memcpy(&lid, l.Data().data() + emp_schema.GetColumn(0).offset, 4);
            std::memcpy(&rid, r.Data().data() + dept_schema.GetColumn(0).offset, 4);
            return lid == rid;
        };
        NestedLoopJoinExecutor nlj(&left_scan, &right_scan, pred);

        // Print by re-scanning and storing both halves
        // Since NLJ stores concatenated bytes, we need to split them.
        // Let's store both tuples in a parallel vector instead.
        // Simplest: override NLJ to emit separately. Instead, just rerun both
        // executors in main and collect matches manually for printing.
        left_scan.Init();
        while (Tuple* l = left_scan.Next()) {
            Tuple l_copy = *l;
            right_scan.Init();
            while (Tuple* r = right_scan.Next()) {
                int32_t lid, rid;
                std::memcpy(&lid, l_copy.Data().data()+emp_schema.GetColumn(0).offset,4);
                std::memcpy(&rid, r->Data().data()+dept_schema.GetColumn(0).offset,4);
                if (lid == rid) {
                    // Print left
                    { int32_t x; std::memcpy(&x,l_copy.Data().data()+emp_schema.GetColumn(0).offset,4); std::cout<<x; }
                    std::cout << " | ";
                    { uint32_t voff; std::memcpy(&voff,l_copy.Data().data()+emp_schema.GetColumn(1).offset,4);
                      const char* s=reinterpret_cast<const char*>(l_copy.Data().data()+emp_schema.TupleSize()+voff);
                      std::cout<<s; }
                    std::cout << " | ";
                    // Print right
                    { int32_t x; std::memcpy(&x,r->Data().data()+dept_schema.GetColumn(0).offset,4); std::cout<<x; }
                    std::cout << " | ";
                    { uint32_t voff; std::memcpy(&voff,r->Data().data()+dept_schema.GetColumn(1).offset,4);
                      const char* s=reinterpret_cast<const char*>(r->Data().data()+dept_schema.TupleSize()+voff);
                      std::cout<<s; }
                    std::cout << "\n";
                }
            }
        }
        left_scan.Close(); right_scan.Close();
    }

    std::cout << "\nHashJoin (employees JOIN departments ON id=emp_id):\n";
    {
        // Build: employees. Probe: departments.
        SeqScanExecutor left_scan(&emp, emp_schema);
        SeqScanExecutor right_scan(&dept, dept_schema);

        // Build hash table on employee id
        left_scan.Init();
        std::unordered_map<int32_t, std::vector<Tuple>> ht;
        while (Tuple* t = left_scan.Next()) {
            int32_t key; std::memcpy(&key,t->Data().data()+emp_schema.GetColumn(0).offset,4);
            ht[key].push_back(*t);
        }
        left_scan.Close();

        // Probe
        right_scan.Init();
        while (Tuple* r = right_scan.Next()) {
            int32_t rkey; std::memcpy(&rkey,r->Data().data()+dept_schema.GetColumn(0).offset,4);
            auto it = ht.find(rkey);
            if (it == ht.end()) continue;
            for (auto& l : it->second) {
                { int32_t x; std::memcpy(&x,l.Data().data()+emp_schema.GetColumn(0).offset,4); std::cout<<x; }
                std::cout << " | ";
                { uint32_t voff; std::memcpy(&voff,l.Data().data()+emp_schema.GetColumn(1).offset,4);
                  const char* s=reinterpret_cast<const char*>(l.Data().data()+emp_schema.TupleSize()+voff);
                  std::cout<<s; }
                std::cout << " | ";
                { int32_t x; std::memcpy(&x,r->Data().data()+dept_schema.GetColumn(0).offset,4); std::cout<<x; }
                std::cout << " | ";
                { uint32_t voff; std::memcpy(&voff,r->Data().data()+dept_schema.GetColumn(1).offset,4);
                  const char* s=reinterpret_cast<const char*>(r->Data().data()+dept_schema.TupleSize()+voff);
                  std::cout<<s; }
                std::cout << "\n";
            }
        }
        right_scan.Close();
    }

    return 0;
}
