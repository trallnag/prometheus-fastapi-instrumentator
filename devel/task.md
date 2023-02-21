# Task

Task is a task runner / build tool that aims to be simpler and easier to use
than, for example, GNU Make.

- [taskfile.dev](https://taskfile.dev)
- [github.com/go-task/task](https://github.com/go-task/task)

Having Task installed is not a hard-requirement for developing. It is mainly
used to collect common scripts / commands.

It can be installed Homebrew (other options are available as well).

```
brew install go-task
```

Task is configured via [`Taskfile.yaml`](../Taskfile.yaml).

When adding new tasks to the task file, try to keep individual tasks simple and
small. More complicated things should be put into individual scripts and then
just called from Task.

## Cheat Sheet

### List tasks

```
task --list
```

### Run task

```
task <task>
```
