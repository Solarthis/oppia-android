import os, pathlib, shutil, subprocess, tempfile, unittest

SOURCE=pathlib.Path(__file__).resolve().parent

class ShellWrappers(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=pathlib.Path(self.tmp.name);self.root=self.base/'renamed checkout';self.scripts=self.root/'scripts';self.scripts.mkdir(parents=True)
        self.bin=self.base/'bin';self.bin.mkdir();self.log=self.base/'calls'
        self.env=dict(os.environ,PATH=str(self.bin)+':/usr/bin:/bin',CALLS=str(self.log))
        for name in ['static_checks.sh','buildifier_lint_check.sh','ktlint_lint_check.sh','formatting.sh']:
            shutil.copy(SOURCE/name,self.scripts/name)
        for name in ['checkstyle_lint_check.sh','buf_lint_check.sh','buildifier_download.sh']:
            self.stub(self.scripts/name,'exit "${CHECK_STATUS:-0}"')
        self.stub(self.bin/'bazel','exit "${BAZEL_STATUS:-0}"')
        self.stub(self.bin/'java','[ "$1" = -jar ] && [ -f "$2" ] || exit 1; exit "${JAVA_STATUS:-0}"')
        self.tools=self.base/'oppia-android-tools';self.tools.mkdir()
        self.stub(self.tools/'buildifier','exit 0');(self.tools/'ktlint').touch()
    def stub(self,path,body):
        path.write_text('#!/bin/bash\nprintf "%s\\n" "'+path.name+'" "$@" >> "$CALLS"\n'+body+'\n');path.chmod(0o755)
    def run_script(self,name,*args,**env):
        return subprocess.run(['bash',str(self.scripts/name),*args],cwd=self.base,env=self.env|env,text=True,capture_output=True)
    def test_buildifier_runs_from_outside_repository(self):
        r=self.run_script('buildifier_lint_check.sh');self.assertEqual(r.returncode,0,r.stderr)
    def test_ktlint_keeps_tool_directory_with_spaces_as_one_argument(self):
        actions=self.base/'actions workspace';tools=actions/'oppia-android-tools';tools.mkdir(parents=True);(tools/'ktlint').touch()
        r=self.run_script('ktlint_lint_check.sh',str(actions));self.assertEqual(r.returncode,0,r.stderr)
    def test_static_check_failure_stops_later_commands(self):
        r=self.run_script('static_checks.sh',CHECK_STATUS='7');self.assertNotEqual(r.returncode,0)
        text=self.log.read_text() if self.log.exists() else '';self.assertNotIn('bazel',text)
    def test_static_checks_allow_renamed_checkout_and_quote_root(self):
        r=self.run_script('static_checks.sh');self.assertEqual(r.returncode,0,r.stderr)
        lines=self.log.read_text().splitlines();self.assertIn(str(self.root),lines)
        self.assertIn('buildifier_download.sh',lines)
    def test_bazel_failure_is_not_masked_by_trailing_echo(self):
        r=self.run_script('static_checks.sh',BAZEL_STATUS='9');self.assertEqual(r.returncode,9)
        self.assertNotIn('//scripts:todo_open_check',self.log.read_text())
    def test_ktlint_failure_stays_failure(self):
        self.assertNotEqual(self.run_script('ktlint_lint_check.sh',JAVA_STATUS='3').returncode,0)
    def test_buildifier_quotes_actions_workspace(self):
        actions=self.base/'actions workspace';tools=actions/'oppia-android-tools';tools.mkdir(parents=True)
        self.stub(tools/'buildifier','exit 0')
        r=self.run_script('buildifier_lint_check.sh',str(actions));self.assertEqual(r.returncode,0,r.stderr)

if __name__=='__main__':unittest.main()
