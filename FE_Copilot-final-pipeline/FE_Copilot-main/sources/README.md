Place input documents here (Markdown/plain-text only) and classify them in
`source_manifest.json`:
- `reverse_method`: reverse-engineered legacy method specs (one file per legacy method,
	or one file per business/technical half of a method — see `contract_unit_group` below)
	or equivalent primary requirements inputs.
- `authoritative_data_model`: authoritative data-model / DDL (required only when
	schema ownership is externally owned).
- `enterprise_architecture` / `standards`: optional supporting docs that constrain
	architecture, interface, and quality decisions.
- `migrated_query`: an already-migrated target-database query (e.g. a PostgreSQL
	query produced by a separate Oracle→PostgreSQL migration process run *before*
	this pipeline). Optional. The 01–08 pipeline never performs or reasons about the
	migration itself — it only consumes the finished artifact as a citable fact
	source for the stages that need query-driven behavior (filtering, sorting,
	pagination) or a deployment-relevant dependency (index/extension). Always
	`unit_profile: NONE`; scope it narrowly with `applies_to_stages` (typically
	`["05","06","07"]` — see PLATFORM_CONTEXT_GUIDE.md). Absence never fails the
	run: stages that would have cited it record an Open Question /
	`DEFERRED-QUERY` note and continue with whatever the reverse-engineering
	sources already state about the query's behavior. Store it as a `.md` file
	wrapping the query text in a fenced code block (this repo's tooling only
	indexes `.md`/plain-text sources), e.g. `migrated_extended_payment_order_query.md`.
- `change_request`: `change_requests.md`.

**Optional field — `contract_unit_group`** (any source type): when one legacy
method's business detail and technical/exception detail are split across two or
more files (rather than one combined `reverse_method` file), give every file in
that split the same `contract_unit_group` value. Stage 01 and stage 05 then treat
all files sharing a group value as **one** requirement/contract unit — merging
and citing all of them — instead of one unit per file. Files without this field
default to a group of one (today's default behavior: one file = one unit).

Deterministic seam gates apply only to files that participate in those seams per
the manifest. Supporting docs can be non-unitized (`unit_profile: NONE`) and are
still valid inputs.

Redact all credential values. `change_requests.md` is the only mutable file after stage 01.
