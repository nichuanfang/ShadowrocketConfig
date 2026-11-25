"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const { loadReleaseItems, publishRelease } = require("../../.github/scripts/gist-publisher.cjs");

function createWorkspace(items) {
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), "shadowrocket-release-"));
  fs.mkdirSync(path.join(workspace, "dist"));
  fs.writeFileSync(
    path.join(workspace, "dist", "release-plan.json"),
    JSON.stringify({ version: 1, items }),
  );
  for (const item of items) {
    fs.mkdirSync(path.dirname(path.join(workspace, item.path)), { recursive: true });
    fs.writeFileSync(path.join(workspace, item.path), `# ${item.id}\nFINAL,PROXY\n`);
  }
  return workspace;
}

function releaseItem(id, secret) {
  return {
    id,
    path: `dist/shadowrocket_${id}.conf`,
    gist_file: `shadowrocket_${id}.conf`,
    gist_secret: secret,
  };
}

test("publishes every profile in manifest order", async () => {
  const workspace = createWorkspace([
    releaseItem("free", "FREE_GIST_ID"),
    releaseItem("black", "BLACK_GIST_ID"),
  ]);
  const calls = [];
  const github = {
    rest: {
      gists: {
        update: async (request) => calls.push(request),
      },
    },
  };

  const count = await publishRelease(
    workspace,
    { FREE_GIST_ID: "free-id", BLACK_GIST_ID: "black-id" },
    github,
  );

  assert.equal(count, 2);
  assert.deepEqual(
    calls.map((call) => [call.gist_id, Object.keys(call.files)[0]]),
    [
      ["free-id", "shadowrocket_free.conf"],
      ["black-id", "shadowrocket_black.conf"],
    ],
  );
  assert.equal(
    calls[1].files["shadowrocket_black.conf"].content,
    "# black\nFINAL,PROXY\n",
  );
});

test("rejects a missing secret before the first API update", async () => {
  const workspace = createWorkspace([
    releaseItem("free", "FREE_GIST_ID"),
    releaseItem("black", "BLACK_GIST_ID"),
  ]);
  const calls = [];
  const github = {
    rest: { gists: { update: async (request) => calls.push(request) } },
  };

  await assert.rejects(
    publishRelease(workspace, { FREE_GIST_ID: "free-id" }, github),
    /BLACK_GIST_ID/,
  );
  assert.equal(calls.length, 0);
});

test("reports the failing profile after an API error", async () => {
  const workspace = createWorkspace([releaseItem("free", "FREE_GIST_ID")]);
  const github = {
    rest: {
      gists: {
        update: async () => {
          throw Object.assign(new Error("server error"), { status: 500 });
        },
      },
    },
  };

  await assert.rejects(
    publishRelease(workspace, { FREE_GIST_ID: "free-id" }, github),
    /free \(shadowrocket_free\.conf\) failed with HTTP 500/,
  );
});

test("does not mutate when a release artifact is empty", () => {
  const workspace = createWorkspace([releaseItem("free", "FREE_GIST_ID")]);
  fs.writeFileSync(path.join(workspace, "dist", "shadowrocket_free.conf"), "");

  assert.throws(
    () => loadReleaseItems(workspace, { FREE_GIST_ID: "free-id" }),
    /empty/,
  );
});
