# Shell wrapper review

Four improvements: static checks stop on a failed command rather than returning the final echo's success; wrappers resolve the repository from their own script location; quoted executable/JAR and repository paths support spaces; Buildifier download uses an absolute script path in a subshell rather than assuming the checkout is named oppia-android.

Seven isolated Python/Bash tests pass. All initial four regressions failed against the original code. Each changed shell file passes Bash syntax checking. Lint executables, Java, Bazel and downloads are synthetic stubs; no downloads, Maven repinning, Android build, learner data or device actions occur in the tests.

`bazel test //...` was attempted but stopped because Bazel is missing (exit 127). Native Android/JVM lint and app suites remain unverified. Existing Maven repin behavior in the full static-check script is unchanged: running that script outside the test harness can still update dependency files. No upstream submission or deployment; this is a draft in the owner's fork.

Run `python3 scripts/test_shell_wrappers.py -v` for the isolated harness.
