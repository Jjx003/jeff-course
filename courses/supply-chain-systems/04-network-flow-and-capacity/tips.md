# Tips

- Build both forward and reverse residual edges.
- In BFS, store each node's parent so you can reconstruct the augmenting path.
- The bottleneck on a path is the minimum residual capacity along that path.
- After augmenting, increase forward flow and decrease reverse flow.
