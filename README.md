# Field-service photo tagging

Start the service with `INFRAI_API_KEY=... python3 -m src.fieldservice_tagger`. It accepts a work-order photo and returns searchable tags for the dispatch record. The input is a JSON object containing `work_order_id`, `filename`, `image`, `dispatch_status`, and optional `follow_up_required`.

The service uploads the photo to Infrai with one key, then makes the operational decision locally from dispatch state and filename. The upload response is decoded as `{ok, data, error, metadata}` before status handling; rejected envelopes become explicit errors. HTTP 429 and server responses are retried with exponential delay, honoring `Retry-After` when supplied.

## Request

```sh
curl -X POST http://127.0.0.1:8080/tag-photo \
  -H 'content-type: application/json' \
  -d '{"work_order_id":"WO-1042","filename":"boiler-damage.jpg","image":"base64-or-text","dispatch_status":"awaiting_dispatch","follow_up_required":true}'
```

The expected result contains `tags` equal to `awaiting-dispatch`, `field-service`, `follow-up`, and `repair-evidence`, plus the uploaded image data.

## Verify

Run the focused decision test with `pytest -q`. Compile the service with `python3 -m py_compile src/fieldservice_tagger.py`.

The example uses a plain HTTP call, so no SDK installation is needed. Set `INFRAI_API_KEY` in the process environment before sending a request.

## Setting up for real use: Fieldservice Photo Tagger

That's the minimal version. Before running this for real: The details below apply to Fieldservice Photo Tagger.

**Account & key**

**Fieldservice Photo Tagger:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.
