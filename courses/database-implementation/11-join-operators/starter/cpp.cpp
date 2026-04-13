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

// ---- Full Tuple/Schema/Value/TableHeap/SeqScanExecutor stack (from module 10) ----

enum class TypeId { INT32, INT64, FLOAT64, VARCHAR };
static size_t TypeSize(TypeId t) {
    switch (t) { case TypeId::INT32: return 4; case TypeId::INT64: return 8;
                 case TypeId::FLOAT64: return 8; case TypeId::VARCHAR: return 4; }
    return 0;
}
struct Column { std::string name; TypeId type; size_t offset; size_t size; };
class Schema {
public:
    Schema(std::initializer_list<std::pair<std::string,TypeId>> cols) {
        size_t off=0;
        for(auto&[n,t]:cols){ size_t sz=TypeSize(t); columns_.push_back({n,t,off,sz}); off+=sz; }
        tuple_size_=off;
    }
    const Column& GetColumn(size_t i) const { return columns_[i]; }
    size_t NumColumns() const { return columns_.size(); }
    size_t TupleSize()  const { return tuple_size_; }
private:
    std::vector<Column> columns_;
    size_t tuple_size_{0};
};
class Value {
public:
    explicit Value(int32_t v):type_(TypeId::INT32),data_(v){}
    explicit Value(std::string v):type_(TypeId::VARCHAR),data_(std::move(v)){}
    TypeId Type() const { return type_; }
    std::string ToString() const {
        return std::visit([](auto&&v)->std::string{
            using T=std::decay_t<decltype(v)>;
            if constexpr(std::is_same_v<T,std::string>)return v;
            else return std::to_string(v);
        },data_);
    }
    int32_t AsInt32() const { return std::get<int32_t>(data_); }
    std::string AsVarchar() const { return std::get<std::string>(data_); }
private:
    TypeId type_;
    std::variant<int32_t,int64_t,double,std::string> data_;
};
class Tuple {
public:
    Tuple()=default;
    Tuple(const Schema& schema, std::initializer_list<Value> values) {
        data_.resize(schema.TupleSize());
        size_t i=0;
        for(const Value& v:values){
            const Column& col=schema.GetColumn(i++);
            switch(col.type){
                case TypeId::INT32:{int32_t x=v.AsInt32();std::memcpy(data_.data()+col.offset,&x,4);break;}
                case TypeId::VARCHAR:{
                    uint32_t voff=static_cast<uint32_t>(data_.size()-schema.TupleSize());
                    std::memcpy(data_.data()+col.offset,&voff,4);
                    for(char c:v.AsVarchar())data_.push_back(static_cast<std::byte>(c));
                    data_.push_back(std::byte{0});break;
                }
                default:break;
            }
        }
    }
    Value GetValue(const Schema& schema, size_t col_idx) const {
        const Column& col=schema.GetColumn(col_idx);
        switch(col.type){
            case TypeId::INT32:{int32_t x;std::memcpy(&x,data_.data()+col.offset,4);return Value{x};}
            case TypeId::VARCHAR:{
                uint32_t voff;std::memcpy(&voff,data_.data()+col.offset,4);
                const char* s=reinterpret_cast<const char*>(data_.data()+schema.TupleSize()+voff);
                return Value{std::string(s)};
            }
            default:return Value{int32_t{0}};
        }
    }
    std::vector<std::byte>& Data() { return data_; }
    const std::vector<std::byte>& Data() const { return data_; }
private:
    std::vector<std::byte> data_;
};
class TableHeap {
public:
    explicit TableHeap(const Schema& s):schema_(s){}
    void InsertTuple(const Tuple& t){tuples_.push_back(t);}
    size_t Size() const{return tuples_.size();}
    const Tuple& GetTuple(size_t i) const{return tuples_[i];}
    const Schema& GetSchema() const{return schema_;}
private:
    const Schema& schema_;
    std::vector<Tuple> tuples_;
};
class AbstractExecutor {
public:
    virtual ~AbstractExecutor()=default;
    virtual void Init()=0;virtual Tuple* Next()=0;virtual void Close()=0;
};
using Predicate=std::function<bool(const Tuple&,const Schema&)>;
class SeqScanExecutor:public AbstractExecutor{
public:
    SeqScanExecutor(TableHeap* t,const Schema& s,Predicate p=nullptr):table_(t),schema_(s),pred_(std::move(p)){}
    void Init() override{idx_=0;}
    void Close() override{}
    Tuple* Next() override{
        while(idx_<table_->Size()){
            current_=table_->GetTuple(idx_++);
            if(!pred_||pred_(current_,schema_))return &current_;
        }
        return nullptr;
    }
private:
    TableHeap* table_;const Schema& schema_;Predicate pred_;
    size_t idx_{0};Tuple current_;
};

// ---------------------------------------------------------------------------
// TODO: Implement NestedLoopJoinExecutor
// ---------------------------------------------------------------------------

class NestedLoopJoinExecutor : public AbstractExecutor {
public:
    NestedLoopJoinExecutor(AbstractExecutor* left, AbstractExecutor* right,
                           std::function<bool(const Tuple&, const Tuple&)> pred)
        : left_(left), right_(right), join_pred_(std::move(pred)) {}

    void Init() override {
        // TODO:
        // 1. Materialise left side into left_tuples_
        // 2. Reset left_idx_ = 0
        // 3. right_->Init(), advance to first right tuple
    }

    Tuple* Next() override {
        // TODO:
        // For each left tuple, iterate right tuples.
        // When right exhausted, advance left and re-init right.
        // Return concatenated tuple when join_pred_ is true.
        return nullptr;
    }

    void Close() override { right_->Close(); }

private:
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
// TODO: Implement HashJoinExecutor
// ---------------------------------------------------------------------------

class HashJoinExecutor : public AbstractExecutor {
public:
    HashJoinExecutor(AbstractExecutor* left, AbstractExecutor* right,
                     std::function<int32_t(const Tuple&)> left_key,
                     std::function<int32_t(const Tuple&)> right_key)
        : left_(left), right_(right),
          left_key_fn_(std::move(left_key)), right_key_fn_(std::move(right_key)) {}

    void Init() override {
        // TODO:
        // 1. Materialise left into hash_table_ keyed by left_key_fn_(t)
        // 2. right_->Init()
        // 3. Reset cur_bucket_ / bucket_idx_
    }

    Tuple* Next() override {
        // TODO:
        // Probe phase: for each right tuple, look up hash_table_[right_key_fn_(r)]
        // Emit matches one at a time as concatenated tuples
        return nullptr;
    }

    void Close() override { right_->Close(); }

private:
    AbstractExecutor* left_;
    AbstractExecutor* right_;
    std::function<int32_t(const Tuple&)> left_key_fn_;
    std::function<int32_t(const Tuple&)> right_key_fn_;
    std::unordered_map<int32_t, std::vector<Tuple>> hash_table_;
    std::vector<Tuple>* cur_bucket_{nullptr};
    size_t bucket_idx_{0};
    Tuple  cur_right_;
    Tuple  current_;
};

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main() {
    Schema emp_schema{{"id",TypeId::INT32},{"name",TypeId::VARCHAR}};
    Schema dept_schema{{"emp_id",TypeId::INT32},{"dept",TypeId::VARCHAR}};

    TableHeap emp(emp_schema);
    emp.InsertTuple(Tuple(emp_schema,{Value{int32_t{1}},Value{std::string{"Alice"}}}));
    emp.InsertTuple(Tuple(emp_schema,{Value{int32_t{2}},Value{std::string{"Bob"}}}));
    emp.InsertTuple(Tuple(emp_schema,{Value{int32_t{3}},Value{std::string{"Carol"}}}));

    TableHeap dept(dept_schema);
    dept.InsertTuple(Tuple(dept_schema,{Value{int32_t{1}},Value{std::string{"Eng"}}}));
    dept.InsertTuple(Tuple(dept_schema,{Value{int32_t{2}},Value{std::string{"Mkt"}}}));
    dept.InsertTuple(Tuple(dept_schema,{Value{int32_t{2}},Value{std::string{"Sales"}}}));

    auto get_emp_id  = [&](const Tuple& t){ int32_t x; std::memcpy(&x,t.Data().data()+emp_schema.GetColumn(0).offset,4); return x; };
    auto get_dept_id = [&](const Tuple& t){ int32_t x; std::memcpy(&x,t.Data().data()+dept_schema.GetColumn(0).offset,4); return x; };

    // Helper: print a tuple given schemas for left and right portions
    // (Left and right data are concatenated in the result tuple)
    auto print_result = [&](Tuple* t, const Schema& ls, const Schema& rs) {
        for (size_t i = 0; i < ls.NumColumns(); ++i) {
            if (i > 0) std::cout << " | ";
            const Column& col = ls.GetColumn(i);
            switch (col.type) {
                case TypeId::INT32: { int32_t x; std::memcpy(&x,t->Data().data()+col.offset,4); std::cout<<x; break; }
                case TypeId::VARCHAR: { uint32_t voff; std::memcpy(&voff,t->Data().data()+col.offset,4);
                    const char* s=reinterpret_cast<const char*>(t->Data().data()+ls.TupleSize()+voff); std::cout<<s; break; }
                default: break;
            }
        }
        // Right portion starts after left full data — but size varies.
        // TODO: print right columns
        std::cout << "\n";
    };
    (void)print_result;

    // NLJ
    std::cout << "NestedLoopJoin (employees JOIN departments ON id=emp_id):\n";
    {
        SeqScanExecutor ls(&emp, emp_schema);
        SeqScanExecutor rs(&dept, dept_schema);
        auto join_pred = [&](const Tuple& l, const Tuple& r) {
            return get_emp_id(l) == get_dept_id(r);
        };
        NestedLoopJoinExecutor nlj(&ls, &rs, join_pred);
        nlj.Init();
        while (Tuple* t = nlj.Next()) {
            // TODO: print t (you may need to split left/right portions)
            (void)t;
            std::cout << "row\n";
        }
        nlj.Close();
    }

    // HashJoin
    std::cout << "\nHashJoin (employees JOIN departments ON id=emp_id):\n";
    {
        SeqScanExecutor ls(&emp, emp_schema);
        SeqScanExecutor rs(&dept, dept_schema);
        HashJoinExecutor hj(&ls, &rs, get_emp_id, get_dept_id);
        hj.Init();
        while (Tuple* t = hj.Next()) {
            (void)t;
            std::cout << "row\n";
        }
        hj.Close();
    }

    return 0;
}
