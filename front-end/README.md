# front-end

This project is bootstrapped by [aurelia/new](https://github.com/aurelia/new).

## Do not start the Python API from here

The FastAPI app lives in **`../services/`**. If your prompt ends with `front-end %`, **do not** run `uvicorn app.main:app` in this directory — you will get `ModuleNotFoundError: No module named 'app'`.

From the repo root use **`./services/run-dev.sh`**, or:

```bash
cd ../services && source .venv/bin/activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Prototype data (same file as the API)

Seeded users, rides, saved addresses, and map stub suggestions all come from the repo file **`../references/data/synthetic-data.json`**. After a fresh DB seed, every user’s password is **`demo`** (see root `README.md`). Example passenger sign-in: **`sophie.zhang@gmail.com`**. The booking form’s default pickup and destination in `src/my-app.js` match Sophie’s first completed ride and her Home / Work saved addresses in that JSON.

## Quick start

    npm install
    npm start

Run unit tests:

    npm test

## Start dev web server

    npm start

## Build the app in production mode

    npm run build


## Unit Tests

    npm run test

Run unit tests in watch mode.

    npm run test:watch

