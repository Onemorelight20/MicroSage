# Migration to pnpm

This project has been migrated from npm to pnpm for better performance and disk space efficiency.

## What Changed

### Files Added
- `frontend/pnpm-lock.yaml` - pnpm's lockfile (committed to git)
- `frontend/.npmrc` - pnpm configuration file

### Files Removed
- `frontend/package-lock.json` - npm's lockfile (no longer needed)
- `frontend/yarn.lock` - yarn's lockfile (if it existed)

### Documentation Updated
- `WEB_UI_SETUP.md` - All npm commands replaced with pnpm commands
- `.gitignore` - Updated to exclude pnpm-specific files

## Using pnpm

### Installation
If you don't have pnpm installed:
```bash
npm install -g pnpm
```

### Common Commands

#### Install dependencies
```bash
cd frontend
pnpm install
```

#### Start development server
```bash
cd frontend
pnpm start
```

#### Build for production
```bash
cd frontend
pnpm run build
```

#### Add a new dependency
```bash
cd frontend
pnpm add <package-name>
```

#### Add a dev dependency
```bash
cd frontend
pnpm add -D <package-name>
```

#### Update dependencies
```bash
cd frontend
pnpm update
```

#### Remove a dependency
```bash
cd frontend
pnpm remove <package-name>
```

## Why pnpm?

1. **Faster** - pnpm installs packages significantly faster than npm
2. **Efficient** - Uses a content-addressable storage, saving disk space
3. **Strict** - Better dependency resolution and prevents phantom dependencies
4. **Compatible** - Works with the same package.json as npm

## Configuration

The `.npmrc` file in the frontend directory contains:
- `auto-install-peers=true` - Automatically installs peer dependencies
- `strict-peer-dependencies=false` - Allows some flexibility with peer deps (needed for React Scripts)
- `shamefully-hoist=true` - Provides better compatibility with tools that expect flat node_modules

## Troubleshooting

### Clear pnpm cache
```bash
pnpm store prune
```

### Reinstall all dependencies
```bash
cd frontend
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### Check pnpm version
```bash
pnpm --version
```

### Update pnpm
```bash
npm install -g pnpm@latest
```

## For Contributors

When contributing to this project:
1. Use `pnpm` instead of `npm` or `yarn`
2. Commit the `pnpm-lock.yaml` file with your changes
3. Do not commit `package-lock.json` or `yarn.lock`
4. Make sure you have pnpm v8.0 or higher installed

## Migration Date
October 19, 2025

## Current Version
- pnpm: 10.18.3
- Node.js: 16+ required

