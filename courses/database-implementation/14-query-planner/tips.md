# Tips: Query Planner

- **Tokenization strategy** — replace commas with spaces (`std::replace`), then use
  `std::istringstream` to split on whitespace.  You get a clean `vector<string>` of
  tokens with zero pointer arithmetic.

- **Multi-char operators** — after you see `<` or `>` as a token, check if the *next*
  character is `=`.  Since you've already split on whitespace, `<=` and `>=` will already
  arrive as single tokens if there is no space around them.  If the user writes
  `salary > 80000`, you get three tokens: `salary`, `>`, `80000`.  Either way, check
  whether the operator token ends with `=`.

- **Case-insensitive keywords** — convert each token to uppercase before comparing to
  `"SELECT"`, `"FROM"`, `"WHERE"`.  Column names and table names remain as-is.

- **`Projector` owns its buffer** — keep a `std::vector<int64_t> buf_` member in
  `Projector`.  Each call to `Next()` fills `buf_` from the child row and returns
  `&buf_`.  Do not return a pointer to a local variable.

- **`InMemorySeqScan` cursor** — use a `size_t index_` member initialized to 0 in
  `Init()`.  `Next()` advances the cursor and skips rows that fail the filter.

- **Blank line after each query** — the `Execute` function should print `"\n"` after
  printing all rows, giving the empty line separator shown in the expected output.

- **`std::string_view` for tokenization** — if you want zero-copy tokenization,
  `string_view` lets you slice into the original SQL string.  For this problem size it
  does not matter, but it is a good habit.

- **Keep the planner thin** — `BuildPlan` should do nothing clever: resolve indices,
  construct two executor objects, wire them together.  All the complexity lives in
  `ParseSQL`.
