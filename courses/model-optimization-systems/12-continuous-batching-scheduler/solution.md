# Solution walkthrough

The important detail is admission at token boundaries. Request B finishes after one tick, so request C can enter at the next tick while A continues.

Real serving engines also schedule prefill chunks, manage KV-cache pages, and stream output, but this toy captures the central idea.

