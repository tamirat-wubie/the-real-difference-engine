# API Design

Future endpoints.

## POST /compare

Input:

- a
- b
- lens
- context
- depth
- output_type

Output:

- comparison object
- generated artifact

## POST /validate

Input:

- comparison object

Output:

- valid/invalid
- errors
- warnings

## POST /generate

Input:

- comparison object
- output type

Output:

- short script
- long outline
- newsletter
- report

## GET /comparisons

Returns stored comparison objects.

## POST /requests

Stores audience comparison requests.
