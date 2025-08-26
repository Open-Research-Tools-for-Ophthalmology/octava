# Octava
## Set-up
Hi everyone, welcome to the repository, please clone the repository to your device first. When developing, please create a new feature branch from `main`. Before you resume your work, run `git pull origin main` to download updates from `main` to your feature branch. And when creating pull requests, merge your feature branch into `main`. 

Source code is placed under the folder `source` for the ease of development (please try not to change the source files), please place our Python code in the folder `code`.


One example:
If you’re working on a new feature or fix:
- You should base your work on main.
- Therefore, fetch from origin and create your new feature branch.
```
git fetch origin
git checkout main
git pull origin main   # updates your local main
git checkout -b feature/your-feature-name
```

## Note
The slicing differences between Python and Matlab:
- In MATLAB, 1:m includes the m-th element; index starts at 1.
- In Python, 0:m includes up to m-1; index starts at 0.
