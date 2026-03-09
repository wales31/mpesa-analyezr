const fs = require('fs');
const path = require('path');

const settingsFile = path.join(
  __dirname,
  '..',
  'node_modules',
  '@react-native',
  'gradle-plugin',
  'settings.gradle.kts'
);

if (!fs.existsSync(settingsFile)) {
  console.log('[patch-react-native-gradle-plugin] file not found, skipping:', settingsFile);
  process.exit(0);
}

const original = fs.readFileSync(settingsFile, 'utf8');
const pluginRegex = /plugins\s*\{\s*id\("org\.gradle\.toolchains\.foojay-resolver-convention"\)\.version\("[^"]+"\)\s*\}/m;

if (!pluginRegex.test(original)) {
  console.log('[patch-react-native-gradle-plugin] no foojay plugin block found; nothing to patch.');
  process.exit(0);
}

const patched = original.replace(
  pluginRegex,
  `// Patched by mobile/scripts/patch-react-native-gradle-plugin.js\n// The foojay resolver plugin can fail on some Gradle/JDK combinations\n// (e.g. missing JvmVendorSpec constants such as IBM_SEMERU).\nplugins {}`
);

fs.writeFileSync(settingsFile, patched, 'utf8');
console.log('[patch-react-native-gradle-plugin] patched', settingsFile);
