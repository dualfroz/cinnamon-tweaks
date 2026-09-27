import atexit
import os
import shutil
import subprocess
import tempfile

testSchemaId = "org.example.shortcutmanager.test"

testSchemaXml = f"""<schemalist>
  <schema id="{testSchemaId}" path="/org/example/shortcutmanager/test/">
    <key name="terminal" type="as"><default>['&lt;Primary&gt;&lt;Alt&gt;t']</default></key>
    <key name="lock" type="as"><default>['&lt;Super&gt;l', '&lt;Control&gt;&lt;Alt&gt;l']</default></key>
    <key name="enabled" type="b"><default>true</default></key>
  </schema>
</schemalist>
"""

schemaDir = tempfile.mkdtemp(prefix="shortcut-manager-test-")
atexit.register(shutil.rmtree, schemaDir, True)

schemaCompiled = False
if shutil.which("glib-compile-schemas"):
    with open(os.path.join(schemaDir, f"{testSchemaId}.gschema.xml"), "w") as schemaFile:
        schemaFile.write(testSchemaXml)
    schemaCompiled = subprocess.run(["glib-compile-schemas", schemaDir], capture_output=True).returncode == 0

os.environ["GSETTINGS_SCHEMA_DIR"] = schemaDir
os.environ["GSETTINGS_BACKEND"] = "memory"
