# Solution walkthrough

The toy adapter is larger than the dense matrix because the matrix is tiny. In real transformer projections, dimensions are thousands wide and ranks are usually small, so the adapter percentage becomes tiny.

The merge step is just matrix addition after computing the low-rank delta. Production systems care because a merged adapter avoids extra adapter operations at inference time.

