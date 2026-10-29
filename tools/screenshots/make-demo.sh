#!/bin/sh
# Builds the demo project the README screenshots show: a small music app with a varied file tree
# (for icons), a TypeScript file (for code colors), a short git history (for terminal colors) and
# data/music.db (for the SQLite Browser).
# Usage: tools/screenshots/make-demo.sh <new directory>
set -eu

if [ $# -ne 1 ] || [ -e "$1" ]; then
  echo "usage: $0 <new directory>" >&2
  exit 2
fi
mkdir -p "$1"
cd "$1"
mkdir -p .github/workflows .vscode data docs public scripts src/components src/lib test worker/src

cat > package.json <<'EOF'
{
  "name": "tidepool",
  "version": "0.4.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "vite": "^6.0.0",
    "vitest": "^2.1.0"
  }
}
EOF

cat > src/server.ts <<'EOF'
import { createServer } from 'node:http'
import { openDatabase, type Track } from './lib/db'

const PORT = Number(process.env.PORT ?? 8080)
const MAX_RESULTS = 50

interface SearchQuery {
  text: string
  genre?: 'ambient' | 'jazz' | 'synthwave'
  limit: number
}

/** Parses `?q=` and `?genre=` from a request URL, with safe defaults. */
function parseQuery(url: URL): SearchQuery {
  const limit = Math.min(Number(url.searchParams.get('limit') ?? 20), MAX_RESULTS)
  return { text: url.searchParams.get('q')?.trim() ?? '', limit }
}

const db = await openDatabase('data/music.db')

createServer(async (req, res) => {
  const url = new URL(req.url ?? '/', `http://localhost:${PORT}`)
  if (url.pathname !== '/search') {
    res.writeHead(404).end('Not found')
    return
  }
  const query = parseQuery(url)
  const tracks: Track[] = await db.searchTracks(query.text, query.limit)
  // Durations are stored in milliseconds; clients want m:ss.
  const body = tracks.map((t) => ({ ...t, length: formatDuration(t.milliseconds) }))
  res.writeHead(200, { 'content-type': 'application/json' })
  res.end(JSON.stringify(body))
}).listen(PORT, () => console.log(`tidepool listening on :${PORT}`))

export function formatDuration(ms: number): string {
  const seconds = Math.round(ms / 1000)
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
}
EOF

cat > src/lib/db.ts <<'EOF'
export interface Track {
  id: number
  name: string
  album: string
  milliseconds: number
}

export async function openDatabase(path: string) {
  const { DatabaseSync } = await import('node:sqlite')
  const db = new DatabaseSync(path, { readOnly: true })
  const search = db.prepare(
    'SELECT t.id, t.name, a.title AS album, t.milliseconds FROM tracks t JOIN albums a ON a.id = t.album_id WHERE t.name LIKE ? LIMIT ?'
  )
  return {
    searchTracks: async (text: string, limit: number) => search.all(`%${text}%`, limit) as Track[]
  }
}
EOF

cat > src/components/Player.tsx <<'EOF'
import { useState } from 'react'

export function Player({ title }: { title: string }) {
  const [playing, setPlaying] = useState(false)
  return (
    <button className="player" onClick={() => setPlaying(!playing)}>
      {playing ? 'Pause' : 'Play'} {title}
    </button>
  )
}
EOF

cat > src/main.tsx <<'EOF'
import { createRoot } from 'react-dom/client'
import { Player } from './components/Player'
import './styles.css'

createRoot(document.getElementById('root')!).render(<Player title="Low Tide" />)
EOF

cat > src/styles.css <<'EOF'
.player {
  border-radius: 999px;
  padding: 8px 16px;
}
EOF

cat > src/env.d.ts <<'EOF'
/// <reference types="vite/client" />
EOF

cat > test/server.test.ts <<'EOF'
import { expect, test } from 'vitest'
import { formatDuration } from '../src/server'

test('formats durations as m:ss', () => {
  expect(formatDuration(185_000)).toBe('3:05')
})
EOF

cat > worker/src/main.rs <<'EOF'
fn main() {
    println!("tidepool worker: indexing tracks");
}
EOF
cat > worker/Cargo.toml <<'EOF'
[package]
name = "tidepool-worker"
version = "0.1.0"
edition = "2021"
EOF
cat > worker/Cargo.lock <<'EOF'
version = 4
EOF

cat > scripts/seed.py <<'EOF'
import sqlite3

with sqlite3.connect("data/music.db") as db:
    print(db.execute("SELECT count(*) FROM tracks").fetchone()[0], "tracks")
EOF
cat > scripts/deploy.sh <<'EOF'
#!/bin/sh
set -eu
docker compose up -d --build
EOF
cat > requirements.txt <<'EOF'
rich==13.9.4
EOF

cat > public/logo.svg <<'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#89b4fa"/></svg>
EOF
printf 'demo' > public/favicon.ico
printf 'demo' > public/cover.png

cat > index.html <<'EOF'
<!doctype html>
<html lang="en">
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF

cat > .github/workflows/ci.yml <<'EOF'
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install && pnpm test
EOF
cat > .vscode/settings.json <<'EOF'
{ "editor.formatOnSave": true }
EOF
cat > docs/architecture.md <<'EOF'
# Architecture

The server reads `data/music.db` read-only and serves `/search`.
EOF
cat > data/schema.sql <<'EOF'
-- See tools/screenshots/make-demo.sh for the full schema.
EOF

cat > README.md <<'EOF'
# tidepool

A tiny music search server and player, used as a demo project.
EOF
cat > CHANGELOG.md <<'EOF'
# Changelog

## 0.4.0
- Playlists
EOF
printf 'MIT License\n' > LICENSE
printf 'node_modules\ndist\n.env\n' > .gitignore
printf 'PORT=8080\n' > .env.example
printf '{ "semi": false, "singleQuote": true }\n' > .prettierrc
printf 'root = true\n' > .editorconfig
printf '22\n' > .nvmrc
printf 'export default []\n' > eslint.config.js
printf "import { defineConfig } from 'vite'\n\nexport default defineConfig({})\n" > vite.config.ts
printf "import { defineConfig } from 'vitest/config'\n\nexport default defineConfig({})\n" > vitest.config.ts
printf '{ "compilerOptions": { "strict": true, "jsx": "react-jsx" } }\n' > tsconfig.json
printf 'lockfileVersion: 9.0\n' > pnpm-lock.yaml
printf 'FROM node:22-alpine\nCOPY . /app\nCMD ["node", "/app/dist/server.js"]\n' > Dockerfile
printf 'services:\n  app:\n    build: .\n    ports: ["8080:8080"]\n' > docker-compose.yml
printf 'dev:\n\tpnpm dev\n' > Makefile
printf 'module example.com/tidepool\n\ngo 1.23\n' > go.mod

# The music database: invented artists, albums and tracks, plus a view, an index and a trigger so
# the SQLite Browser sidebar shows every kind of object.
sqlite3 data/music.db >/dev/null <<'EOF'
PRAGMA journal_mode = DELETE;
CREATE TABLE artists (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  country TEXT,
  formed INTEGER
);
CREATE TABLE albums (
  id INTEGER PRIMARY KEY,
  artist_id INTEGER NOT NULL REFERENCES artists(id),
  title TEXT NOT NULL,
  released TEXT,
  genre TEXT
);
CREATE TABLE tracks (
  id INTEGER PRIMARY KEY,
  album_id INTEGER NOT NULL REFERENCES albums(id),
  track_no INTEGER NOT NULL,
  name TEXT NOT NULL,
  milliseconds INTEGER NOT NULL,
  plays INTEGER NOT NULL DEFAULT 0,
  rating REAL
);
CREATE TABLE playlists (id INTEGER PRIMARY KEY, name TEXT NOT NULL, updated_at TEXT);
CREATE TABLE playlist_tracks (
  playlist_id INTEGER REFERENCES playlists(id),
  track_id INTEGER REFERENCES tracks(id),
  position INTEGER,
  PRIMARY KEY (playlist_id, track_id)
);
CREATE INDEX tracks_by_album ON tracks(album_id, track_no);
CREATE TRIGGER playlists_touch AFTER INSERT ON playlist_tracks
BEGIN
  UPDATE playlists SET updated_at = datetime('now') WHERE id = NEW.playlist_id;
END;
CREATE VIEW album_stats AS
  SELECT ar.name AS artist, al.title AS album, al.genre, count(t.id) AS tracks,
         sum(t.plays) AS plays, round(avg(t.rating), 2) AS avg_rating
  FROM albums al
  JOIN artists ar ON ar.id = al.artist_id
  JOIN tracks t ON t.album_id = al.id
  GROUP BY al.id
  ORDER BY plays DESC;

INSERT INTO artists (id, name, country, formed) VALUES
  (1, 'The Velvet Tides', 'United Kingdom', 2011),
  (2, 'Neon Harbor', 'Canada', 2016),
  (3, 'Marisol Quintero', 'Mexico', 2009),
  (4, 'Glass Orchard', 'United States', 2014),
  (5, 'Kōhaku', 'Japan', 2018),
  (6, 'Saltwater Choir', 'Ireland', 2012),
  (7, 'Andromeda Lane', 'Australia', 2019),
  (8, 'Fjordlight', 'Norway', 2010),
  (9, 'Copper & Pine', 'United States', 2015),
  (10, 'Lumen Atlas', 'Germany', 2017),
  (11, 'Café Meridian', 'France', 2013),
  (12, 'Paper Satellites', 'New Zealand', 2020);

WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n WHERE i < 30)
INSERT INTO albums (id, artist_id, title, released, genre)
SELECT i,
       (i - 1) % 12 + 1,
       json_extract('["Low Tide","Midnight Static","Paper Moons","Coastlines","Golden Hour","Afterglow","Slow Orbit","Northern Lights","Velvet Rooms","Signal Fires","Open Water","Glasshouse","Driftwood","Satellite Hearts","Blue Hours","Wildflower","Night Ferry","Summer Static","Lantern","Echo Valley","Polaroid","Tidal","Soft Machines","Harbor Songs","Cloud Atlas Club","Lowlands","Morning Radio","Starling","Undertow","Constellations"]', '$[' || (i - 1) || ']'),
       date('2014-03-01', '+' || (i * 97) || ' days'),
       json_extract('["synthwave","indie","jazz","ambient","folk","electronic"]', '$[' || (i % 6) || ']')
FROM n;

WITH RECURSIVE n(i) AS (SELECT 0 UNION ALL SELECT i + 1 FROM n WHERE i < 359)
INSERT INTO tracks (album_id, track_no, name, milliseconds, plays, rating)
SELECT i / 12 + 1,
       i % 12 + 1,
       json_extract('["Silver","Quiet","Electric","Hollow","Golden","Restless","Paper","Distant","Velvet","Wild","Neon","Gentle","Burning","Cold","Hidden","Last"]', '$[' || ((i * 7) % 16) || ']')
         || ' ' ||
       json_extract('["Harbor","Signal","Morning","Rivers","Static","Lanterns","Echoes","Avenue","Weather","Satellites","Gardens","Window","Coast","Summer","Machines","Letters","Highway","Tide"]', '$[' || ((i * 5 + i / 16) % 18) || ']'),
       150000 + (i * 7919) % 180000,
       (i * 104729) % 250000 + (12 - i % 12) * 3000,
       round(3 + ((i * 37) % 21) / 10.0, 1)
FROM n;

INSERT INTO playlists (id, name) VALUES (1, 'Focus'), (2, 'Road Trip'), (3, 'Late Night');
WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM n WHERE i < 45)
INSERT INTO playlist_tracks (playlist_id, track_id, position)
SELECT (i - 1) % 3 + 1, (i * 53) % 360 + 1, (i - 1) / 3 + 1 FROM n;
EOF

# A short history with one merged branch, so `git log --graph` has some shape.
commit() {
  GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git -c user.name='Tidepool' -c user.email='dev@tidepool.example' commit -q --allow-empty -m "$2"
}
git init -q -b main
git add -A
commit '2026-09-02T10:00:00' 'Initial server and player'
commit '2026-09-09T15:30:00' 'Search tracks by name'
git checkout -q -b playlists
commit '2026-09-12T11:00:00' 'Add playlists table and trigger'
commit '2026-09-14T17:45:00' 'Show playlists in the player'
git checkout -q main
commit '2026-09-13T09:20:00' 'Format durations as m:ss'
GIT_AUTHOR_DATE='2026-09-15T12:00:00' GIT_COMMITTER_DATE='2026-09-15T12:00:00' git -c user.name='Tidepool' -c user.email='dev@tidepool.example' merge -q --no-ff -m 'Merge branch playlists' playlists
git tag v0.4.0
commit '2026-09-20T08:10:00' 'Rust worker for indexing'
echo "demo project ready: $(pwd)"
