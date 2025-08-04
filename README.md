# Octava
## Set-up
Hi everyone, welcome to the repository, please clone the repository to your device first. When developing, please create a new feature branch from `dev`. Do not work on `main` branch directly (this helps prevent accidental merges). Before you resume your work, run `git pull origin dev` to download updates from `dev` to your feature branch. And when creating pull requests, merge your feature branch into `dev`. The `main` branch can be updated from `dev` periodically. 

Explanations of `main` and `dev`:
- main: Production-ready code
- dev: Stable development integration branch


Source code is placed under the folder `source` for the ease of development (please try not to change the source files), please place our Python code in the folder `code`.


One example:
If you’re working on a new feature or fix:
- You should base your work on dev.
- Therefore, fetch from origin and update your local dev.
```
git fetch origin
git checkout dev
git pull origin dev   # updates your local dev
git checkout -b feature/your-feature-name
```

## Note
The slicing differences between Python and Matlab:
- In MATLAB, 1:m includes the m-th element; index starts at 1.
- In Python, 0:m includes up to m-1; index starts at 0.
