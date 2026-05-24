# Pre-Commit Hooks Reference

Detailed reference for Husky + lint-staged setup.

## Files Created

### `.husky/pre-commit`
```bash
npx lint-staged
npm run typecheck
npm run test
```

### `.lintstagedrc`
```json
{
  "*": "prettier --ignore-unknown --write"
}
```

### `.prettierrc`
```json
{
  "useTabs": false,
  "tabWidth": 2,
  "printWidth": 80,
  "singleQuote": false,
  "trailingComma": "es5",
  "semi": true,
  "arrowParens": "always"
}
```

## Hook Execution Order

```
git commit
    ↓
Husky pre-commit hook
    ↓
lint-staged (formats staged files)
    ↓
typecheck (type checking)
    ↓
test (run tests)
    ↓
All pass → commit succeeds
Any fail → commit blocked
```

## Customization

### Add More Linters

Edit `.husky/pre-commit`:
```bash
npx lint-staged
npm run typecheck
npm run test
npm run lint  # add ESLint
npx commitlint --edit # add commitlint
```

### Change File Patterns

Edit `.lintstagedrc`:
```json
{
  "*.ts": "prettier --write",
  "*.tsx": "prettier --write",
  "*.md": "prettier --write",
  "*.json": "prettier --write"
}
```

### Skip Hooks (Temporary)

```bash
git commit --no-verify  # bypass pre-commit
```

## Troubleshooting

### Hook not running?
```bash
# Check hook is executable
ls -la .husky/pre-commit

# Re-init if needed
npx husky install
```

### lint-staged not found?
```bash
npm install lint-staged --save-dev
```

### Prettier not formatting?
```bash
# Check Prettier is installed
npm install prettier --save-dev

# Run manually to test
npx prettier --write src/
```

## Package Manager Commands

| Manager | Install | Run lint-staged |
|---------|---------|-----------------|
| npm | `npm install` | `npx lint-staged` |
| pnpm | `pnpm install` | `pnpm exec lint-staged` |
| yarn | `yarn install` | `yarn lint-staged` |
| bun | `bun install` | `bun x lint-staged` |