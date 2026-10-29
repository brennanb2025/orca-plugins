"""Builds plugins/material-icons from an unpacked Material Icon Theme VSIX.

Usage: python3 -I tools/material-icons-build.py <unpacked-vsix>/extension plugins/material-icons

Orca icon themes allow 512 mappings (file, folder and folder-open count toward them), 512 SVGs
and a 64 KiB theme file, and match exact file names, then the longest dotted extension. They
have no per-folder icons and no light variants, so this keeps the most common files only.
"""
import json, os, re, shutil, sys

src, out = sys.argv[1], sys.argv[2]
m = json.load(open(os.path.join(src, 'dist/material-icons.json')))
defs = m['iconDefinitions']

# VS Code picks most language icons by language id, which Orca doesn't have; these are the
# extensions VS Code assigns to each id.
LANG = {
    'typescript': 'ts mts cts', 'typescriptreact': 'tsx', 'javascript': 'js mjs cjs',
    'javascriptreact': 'jsx', 'python': 'py pyi pyw', 'go': 'go', 'rust': 'rs', 'java': 'java',
    'kotlin': 'kt kts', 'swift': 'swift', 'c': 'c', 'cpp': 'cpp cc cxx hpp hh hxx', 'csharp': 'cs',
    'fsharp': 'fs fsi fsx', 'ruby': 'rb', 'php': 'php', 'shellscript': 'sh bash zsh', 'powershell': 'ps1 psm1',
    'html': 'html htm', 'css': 'css', 'scss': 'scss', 'sass': 'sass', 'less': 'less', 'json': 'json',
    'jsonc': 'jsonc', 'json5': 'json5', 'yaml': 'yaml yml', 'xml': 'xml', 'markdown': 'md markdown',
    'sql': 'sql', 'lua': 'lua', 'perl': 'pl pm', 'r': 'r', 'dart': 'dart', 'scala': 'scala sc',
    'clojure': 'clj cljs cljc edn', 'elixir': 'ex exs', 'erlang': 'erl', 'haskell': 'hs', 'ocaml': 'ml mli',
    'objective-c': 'm', 'objective-cpp': 'mm', 'groovy': 'groovy gradle', 'dockerfile': 'dockerfile',
    'makefile': 'mk', 'bat': 'bat cmd', 'ini': 'ini', 'toml': 'toml', 'vue': 'vue', 'svelte': 'svelte',
    'astro': 'astro', 'graphql': 'graphql gql', 'prisma': 'prisma', 'terraform': 'tf tfvars', 'hcl': 'hcl',
    'zig': 'zig', 'nim': 'nim', 'julia': 'jl', 'vb': 'vb', 'coffeescript': 'coffee', 'handlebars': 'hbs handlebars',
    'pug': 'pug', 'stylus': 'styl', 'tex': 'tex', 'latex': 'tex', 'bibtex': 'bib', 'restructuredtext': 'rst',
    'diff': 'diff patch', 'log': 'log', 'proto3': 'proto', 'proto': 'proto', 'solidity': 'sol', 'nix': 'nix',
    'gleam': 'gleam', 'mdx': 'mdx', 'csv': 'csv', 'tsv': 'tsv', 'plaintext': 'txt', 'jinja': 'jinja j2',
    'twig': 'twig', 'razor': 'cshtml', 'vala': 'vala', 'd': 'd', 'crystal': 'cr', 'fortran': 'f90 f95 f',
    'cuda-cpp': 'cu cuh', 'glsl': 'glsl vert frag', 'hlsl': 'hlsl', 'wgsl': 'wgsl', 'odin': 'odin', 'v': 'v',
    'purescript': 'purs', 'elm': 'elm', 'reason': 're rei', 'rescript': 'res resi', 'haxe': 'hx',
    'cmake': 'cmake', 'bicep': 'bicep', 'nunjucks': 'njk', 'ejs': 'ejs', 'liquid': 'liquid', 'hurl': 'hurl',
    'http': 'http rest', 'jsonl': 'jsonl ndjson', 'ignore': '', 'git-commit': '', 'git-rebase': '',
}

# Common extensions and compound suffixes, most common first. Anything Material doesn't map is skipped.
EXTENSIONS = '''
ts tsx js jsx mjs cjs mts cts d.ts json jsonc json5 md mdx py go rs java kt swift c h cpp hpp cc cs rb php
sh bash zsh fish ps1 html htm css scss sass less vue svelte astro yaml yml toml xml ini env lock sql
graphql gql prisma proto tf hcl dockerfile lua dart scala ex exs erl hs ml clj r jl zig nim gleam sol nix
txt log csv tsv pdf zip gz tgz tar rar 7z dmg exe dll so dylib wasm jar
png jpg jpeg gif svg webp ico bmp tiff avif heic psd ai fig sketch xd
mp3 wav ogg flac m4a mp4 mov avi mkv webm ttf otf woff woff2 eot
spec.ts spec.tsx test.ts test.tsx spec.js test.js spec.jsx test.jsx e2e-spec.ts stories.tsx stories.ts stories.jsx stories.js
module.css module.scss d.mts d.cts min.js min.css map js.map css.map
ipynb pyc pyi whl egg go.mod go.sum cabal gemspec rake erb haml slim twig hbs ejs pug njk liquid jinja j2
tex bib rst adoc org epub doc docx xls xlsx xlsm ods ppt pptx odp key numbers pages rtf
db sqlite sqlite3 db3 parquet avro arrow feather pkl h5 onnx pt pth safetensors
pem crt cer key pub gpg asc p12 pfx csr
iso img vmdk vdi qcow2 ova
bat cmd vbs reg desktop plist entitlements xcconfig pbxproj storyboard xib swiftpm
gradle groovy kts properties pom sbt
cmake mk make ninja bazel bzl
http rest hurl har
patch diff
glsl vert frag hlsl wgsl shader cu cuh metal
cr d f90 hx purs elm re res resi fs fsx vb coffee styl razor cshtml vala odin v
bicep jsonl ndjson editorconfig gitattributes gitkeep gitmodules npmignore dockerignore eslintignore prettierignore
code-workspace sln csproj fsproj vbproj vcxproj xcodeproj xcworkspace
excalidraw drawio mmd mermaid puml plantuml dot gv
ics vcf eml msg
'''.split()

FILENAMES = '''
package.json package-lock.json pnpm-lock.yaml pnpm-workspace.yaml yarn.lock bun.lockb bun.lock .npmrc .nvmrc .node-version
tsconfig.json jsconfig.json tsconfig.base.json tsconfig.node.json tsconfig.app.json
readme.md readme changelog.md changelog license license.md license.txt contributing.md code_of_conduct.md security.md authors
claude.md agents.md .cursorrules copilot-instructions.md
.gitignore .gitattributes .gitmodules .gitkeep .git-blame-ignore-revs .mailmap codeowners
.editorconfig .prettierrc .prettierrc.json .prettierrc.js .prettierrc.yaml .prettierignore prettier.config.js prettier.config.mjs
.eslintrc .eslintrc.js .eslintrc.cjs .eslintrc.json .eslintignore eslint.config.js eslint.config.mjs eslint.config.ts
biome.json biome.jsonc .oxlintrc.json oxlint.json .stylelintrc stylelint.config.js
dockerfile docker-compose.yml docker-compose.yaml compose.yml compose.yaml .dockerignore containerfile
makefile cmakelists.txt justfile taskfile.yml rakefile gemfile gemfile.lock procfile vagrantfile brewfile
cargo.toml cargo.lock rust-toolchain.toml go.mod go.sum go.work
requirements.txt pyproject.toml setup.py setup.cfg pipfile pipfile.lock poetry.lock uv.lock .python-version tox.ini
pom.xml build.gradle build.gradle.kts settings.gradle settings.gradle.kts gradle.properties gradlew
package.swift podfile podfile.lock composer.json composer.lock mix.exs deno.json deno.jsonc
vite.config.ts vite.config.js vite.config.mjs vitest.config.ts vitest.config.js vitest.config.mts
webpack.config.js rollup.config.js rollup.config.mjs esbuild.config.js turbo.json nx.json lerna.json
next.config.js next.config.mjs next.config.ts nuxt.config.ts svelte.config.js astro.config.mjs remix.config.js
tailwind.config.js tailwind.config.ts postcss.config.js postcss.config.mjs postcss.config.cjs
jest.config.js jest.config.ts playwright.config.ts playwright.config.js cypress.config.ts cypress.config.js
babel.config.js .babelrc .swcrc electron-builder.yml electron-builder.json electron.vite.config.ts forge.config.js
vercel.json netlify.toml wrangler.toml fly.toml railway.json render.yaml app.json firebase.json .firebaserc
.env .env.local .env.example .env.development .env.production .env.test
.travis.yml .gitlab-ci.yml azure-pipelines.yml jenkinsfile bitbucket-pipelines.yml
renovate.json .renovaterc dependabot.yml .releaserc release.config.js
.lintstagedrc lint-staged.config.js commitlint.config.js .commitlintrc
devcontainer.json .tool-versions .mise.toml mise.toml flake.nix flake.lock shell.nix default.nix
helmfile.yaml chart.yaml kustomization.yaml skaffold.yaml tiltfile terraform.tfvars .terraform.lock.hcl
robots.txt sitemap.xml favicon.ico manifest.json manifest.webmanifest browserslist .browserslistrc
nodemon.json pm2.config.js ecosystem.config.js .gitpod.yml .replit
schema.prisma openapi.yaml openapi.json swagger.json swagger.yaml
orca-plugin.json orca-catalog.json
'''.split()

budget = 512 - 3
icons_used = {}

def icon_file(icon_id):
    path = defs[icon_id]['iconPath']
    name = os.path.basename(path)
    svg = open(os.path.join(src, 'icons', name)).read()
    # Orca's sanitizer drops <use> and anything outside static shapes; skip icons that need it.
    if re.search(r'<(use|text|image|foreignObject|style|script)\b', svg):
        return None
    if len(svg.encode()) > 64 * 1024:
        return None
    icons_used[name] = svg
    return 'icons/' + name

lang_icon = m['languageIds']
# Material's keys are mixed case (Cargo.toml); Orca matches lowercased names.
file_ext_lc = {k.lower(): v for k, v in m['fileExtensions'].items()}
file_name_lc = {k.lower(): v for k, v in m['fileNames'].items()}
ext_map, name_map = {}, {}
def add(target, key, icon_id):
    if len(ext_map) + len(name_map) >= budget or key in target or icon_id is None:
        return
    if len(icons_used) >= 512 and os.path.basename(defs[icon_id]['iconPath']) not in icons_used:
        return
    rel = icon_file(icon_id)
    if rel:
        target[key] = rel

ext_by_lang = {}
for lang, exts in LANG.items():
    for e in exts.split():
        ext_by_lang.setdefault(e, lang)
for e in EXTENSIONS:
    icon = file_ext_lc.get(e) or lang_icon.get(ext_by_lang.get(e, ''))
    add(ext_map, e, icon)
for n in FILENAMES:
    add(name_map, n, file_name_lc.get(n) or file_ext_lc.get(n.lstrip('.').split('.')[-1]))

slots = {'file': icon_file(m['file']), 'folder': icon_file(m['folder']), 'folder-open': icon_file(m['folderExpanded'])}
theme = {'schemaVersion': 1, 'icons': slots, 'fileNames': name_map, 'fileExtensions': ext_map}
icon_dir = os.path.join(out, 'icons')
if os.path.isdir(icon_dir):
    shutil.rmtree(icon_dir)
os.makedirs(icon_dir)
for name, svg in icons_used.items():
    open(os.path.join(icon_dir, name), 'w').write(svg)
body = json.dumps(theme, indent=1) + '\n'
open(os.path.join(out, 'icons', 'theme.json'), 'w').write(body)
skipped_ext = [e for e in EXTENSIONS if e not in ext_map]
skipped_names = [n for n in FILENAMES if n not in name_map]
print(f'mappings {len(ext_map) + len(name_map) + 3}/512, svgs {len(icons_used)}/512, theme.json {len(body)} bytes')
print('extensions without a Material icon:', ' '.join(skipped_ext))
print('file names without a Material icon:', ' '.join(skipped_names))

# Orca icon themes have no light variant, so ship a second theme that swaps in Material's
# light-background icons (white logos such as Next.js and Vercel vanish on light themes).
light = {}
for section in ('fileExtensions', 'fileNames'):
    for key, icon_id in m['light'].get(section, {}).items():
        base_rel = 'icons/' + os.path.basename(defs[icon_id.replace('_light', '')]['iconPath']) if icon_id.replace('_light', '') in defs else None
        if base_rel:
            light[base_rel] = icon_id
swapped = 0
def to_light(mapping):
    global swapped
    result = {}
    for key, rel in mapping.items():
        icon_id = light.get(rel)
        alt = icon_file(icon_id) if icon_id else None
        if alt:
            swapped += 1
        result[key] = alt or rel
    return result
light_theme = {'schemaVersion': 1, 'icons': slots, 'fileNames': to_light(name_map), 'fileExtensions': to_light(ext_map)}
for name, svg in icons_used.items():
    path = os.path.join(icon_dir, name)
    if not os.path.exists(path):
        open(path, 'w').write(svg)
light_body = json.dumps(light_theme, indent=1) + '\n'
open(os.path.join(out, 'icons', 'theme-light.json'), 'w').write(light_body)
print(f'light theme: {swapped} mappings use light icons, svgs now {len(icons_used)}, theme-light.json {len(light_body)} bytes')
