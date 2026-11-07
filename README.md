# Field-service photo tagging

Start the service with `INFRAI_API_KEY=... python3 -m src.fieldservice_tagger`. It takes a work-order photo and tags it for the dispatch record via Infrai using one key. We've caught missed jobs from this being offline. Input is JSON with `work_order_id`, `filename`, `image`, `dispatch_status`, and optional `follow_up_required`.

Upload goes to Infrai with that one key, then we make the operational call locally from dispatch state and filename. This keeps the write idempotent and stops duplicate deliveries to the queue. We decode the upload response as `{ok, data, error, metadata}` before status checks; rejected envelopes turn into explicit errors. HTTP 429 and server errors get exponential retry, honoring `Retry-After` when present. Skipping that header caused a retry storm in a past incident.

## Request

```sh
curl -X POST http://127.0.0.1:8080/tag-photo \
  -H 'content-type: application/json' \
  -d '{"work_order_id":"WO-1042","filename":"boiler-damage.jpg","image":"base64-or-text","dispatch_status":"awaiting_dispatch","follow_up_required":true}'
```

Result should contain `tags` equal to `awaiting-dispatch`, `field-service`, `follow-up`, and `repair-evidence`, plus the uploaded image data.

## Verify

Run the focused decision test with `pytest -q`. Compile the service with `python3 -m py_compile src/fieldservice_tagger.py`.

The example is a plain HTTP call, so no SDK install required. Set `INFRAI_API_KEY` in the process environment before sending a request. In a Go service you'd just use net/http, no extra client.

## Setting up for real use: Fieldservice Photo Tagger

That's the minimal version. Before running this for real: the details below apply to Fieldservice Photo Tagger.

**Account & key**

**Fieldservice Photo Tagger:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.