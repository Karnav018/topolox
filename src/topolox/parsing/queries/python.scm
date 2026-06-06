; Tree-sitter query for Python symbol extraction (Phase 1).
; Captures top-level and nested definitions plus imports.

(function_definition
  name: (identifier) @function.name) @function.def

(class_definition
  name: (identifier) @class.name) @class.def

(import_statement) @import

(import_from_statement) @import
