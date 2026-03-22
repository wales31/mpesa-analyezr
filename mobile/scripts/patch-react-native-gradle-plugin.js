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
const legacyPatchedRegex =
  /\/\/ Patched by mobile\/scripts\/patch-react-native-gradle-plugin\.js[\s\S]*?plugins\s*\{\s*\}/m;
const basePluginRegex =
  /plugins\s*\{\s*id\("org\.gradle\.toolchains\.foojay-resolver"\)\s+version\s+"[^"]+"\s*\}\s*toolchainManagement\s*\{\s*jvm\s*\{\s*javaRepositories\s*\{\s*repository\("foojay"\)\s*\{\s*resolverClass\s*=\s*org\.gradle\.toolchains\.foojay\.FoojayToolchainResolver::class\.java\s*\}\s*\}\s*\}\s*\}/ms;
const replacement = `// Patched by mobile/scripts/patch-react-native-gradle-plugin.js
// Use the base foojay resolver plugin and an explicit repository instead of
// the convention plugin so Gradle can still auto-provision Java toolchains
// without relying on deprecated implicit repository behavior or Gradle 9-removed
// JvmVendorSpec constants such as IBM_SEMERU.
plugins {
    id("org.gradle.toolchains.foojay-resolver") version "0.10.0"
}

toolchainManagement {
    jvm {
        javaRepositories {
            repository("foojay") {
                resolverClass = org.gradle.toolchains.foojay.FoojayToolchainResolver::class.java
            }
        }
    }
}`;

if (basePluginRegex.test(original)) {
  console.log('[patch-react-native-gradle-plugin] foojay toolchain configuration already patched.');
  process.exit(0);
}

if (!pluginRegex.test(original) && !legacyPatchedRegex.test(original)) {
  console.log('[patch-react-native-gradle-plugin] no foojay convention plugin block found; nothing to patch.');
  process.exit(0);
}

const patched = original.replace(pluginRegex, replacement).replace(legacyPatchedRegex, replacement);

fs.writeFileSync(settingsFile, patched, 'utf8');
console.log('[patch-react-native-gradle-plugin] patched', settingsFile);
