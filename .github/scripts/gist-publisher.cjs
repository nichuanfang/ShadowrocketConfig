"use strict";

const fs = require("fs");
const path = require("path");

function readReleasePlan(workspace) {
  const planPath = path.join(workspace, "dist", "release-plan.json");
  const plan = JSON.parse(fs.readFileSync(planPath, "utf8"));

  if (plan.version !== 1 || !Array.isArray(plan.items) || plan.items.length === 0) {
    throw new Error(`Invalid release plan: ${planPath}`);
  }

  return plan;
}

function loadReleaseItems(workspace, environment) {
  const plan = readReleasePlan(workspace);
  const seenSecrets = new Set();

  return plan.items.map((item) => {
    const secretName = item.gist_secret;
    const gistId = environment[secretName];
    if (!gistId) {
      throw new Error(`Missing Gist ID secret for ${item.id}: ${secretName}`);
    }
    if (seenSecrets.has(secretName)) {
      throw new Error(`Duplicate release plan secret: ${secretName}`);
    }
    seenSecrets.add(secretName);

    const sourcePath = path.resolve(workspace, item.path);
    const relativePath = path.relative(path.resolve(workspace), sourcePath);
    if (relativePath.startsWith("..") || path.isAbsolute(relativePath)) {
      throw new Error(`Release artifact escapes the workspace for ${item.id}: ${item.path}`);
    }
    const content = fs.readFileSync(sourcePath, "utf8");
    if (!content.trim()) {
      throw new Error(`Release artifact for ${item.id} is empty: ${item.path}`);
    }

    return {
      id: item.id,
      gistId,
      sourcePath,
      gistFile: item.gist_file,
      content,
    };
  });
}

async function publishRelease(workspace, environment, github) {
  const items = loadReleaseItems(workspace, environment);

  for (const item of items) {
    try {
      await github.rest.gists.update({
        gist_id: item.gistId,
        files: { [item.gistFile]: { content: item.content } },
      });
    } catch (error) {
      throw new Error(
        `${item.id} (${item.gistFile}) failed with HTTP ${error.status}`,
        { cause: error },
      );
    }
    console.log(`Updated ${item.id}: ${item.gistFile}`);
  }

  return items.length;
}

module.exports = { loadReleaseItems, publishRelease, readReleasePlan };
