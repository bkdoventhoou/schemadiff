# schemadiff

A tool to compare and version database schemas across environments with human-readable diffs.

---

## Installation

```bash
pip install schemadiff
```

Or install from source:

```bash
git clone https://github.com/yourusername/schemadiff.git && pip install -e .
```

---

## Usage

Compare two database schemas and output a human-readable diff:

```bash
schemadiff compare --source postgres://user:pass@staging/db \
                   --target postgres://user:pass@production/db
```

Export a schema snapshot for versioning:

```bash
schemadiff snapshot --db postgres://user:pass@localhost/mydb --output schema.json
```

Compare two saved snapshots:

```bash
schemadiff diff schema_v1.json schema_v2.json
```

Example output:

```
[+] Table added:        user_sessions
[~] Table modified:     orders
    [+] Column added:   orders.discount_code (VARCHAR 50)
    [-] Column removed: orders.promo_field
[-] Table removed:      legacy_tokens
```

Use `--format json` to get machine-readable output suitable for CI pipelines.

---

## Supported Databases

- PostgreSQL
- MySQL / MariaDB
- SQLite

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any major changes.

---

## License

This project is licensed under the [MIT License](LICENSE).