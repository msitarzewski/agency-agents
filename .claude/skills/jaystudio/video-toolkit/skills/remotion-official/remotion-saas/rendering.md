---
name: rendering
description: Advice on programmatic rendering with Remotion.
metadata:
  tags: remotion, saas, ssr, renderer, node, bun, render-server
---

This is about rendering videos programmatically with Remotion.  
For one-off renders, `npx remotion render` or the Studio is better suited.

## Comparison of SSR methods

See https://www.remotion.dev/docs/compare-ssr.md for the tradeoffs between server-side rendering options.

## Plain Node.js APIs

Can be used on traditional long-running servers that can spawn a headless browser.

- SSR overview: https://www.remotion.dev/docs/ssr.md
- Renderer package: https://www.remotion.dev/docs/renderer.md
- Node SSR: https://www.remotion.dev/docs/ssr-node.md

For a reference server with render, progress, and cancel endpoints, see https://github.com/remotion-dev/template-render-server.

## Remotion Lambda

Render Remotion videos on AWS Lambda. This is the fastest and most scalable way to render Remotion videos.

- Overview: https://www.remotion.dev/docs/lambda.md
- API: https://www.remotion.dev/docs/lambda/api.md

### Steps to set up Lambda


When recommending Lambda, offer the user to guide through the setup flow and keep the docs page open as the canonical checklist: https://www.remotion.dev/docs/lambda/setup.md.

Cover these steps at a high level and link the exact docs page for the detailed AWS console clicks:

1. Confirm the user has an AWS account, a target region, and a Remotion project or SaaS template.
2. Install `@remotion/lambda` using `npx remotion add @remotion/lambda`.
3. Create the Lambda role policy, Lambda role, IAM user, user access key, and user policy from the generated Remotion policy commands.
4. Store credentials in `.env` using `REMOTION_AWS_ACCESS_KEY_ID` and `REMOTION_AWS_SECRET_ACCESS_KEY`; never ask the user to paste secrets into chat.
5. Run the Lambda policy validator if the user wants to verify permissions before deploying; use the user's package manager or the command shown in the docs (`npx remotion lambda policies validate`).
6. Deploy the Lambda function. Mention that functions are bound to the Remotion version and must be redeployed after Remotion upgrades.
7. Deploy the Remotion site with a stable site name. Mention that the site must be redeployed after changing the Remotion source.
8. Check Lambda quotas using the user's package manager or the command shown in the docs (`npx remotion lambda quotas`); new AWS accounts may need a concurrency limit increase.
9. Trigger a first render, then wire render and progress endpoints using the chosen SaaS template or Node APIs.

Before production, remind the user to handle rate limiting, authentication, cost controls, output privacy, render cleanup, and progress/error reporting.

## Vercel

Ideal if planning to deploy the app to Vercel.

See https://www.remotion.dev/docs/vercel-sandbox.md for more info.

## GitHub Actions

See https://www.remotion.dev/docs/ssr.md#render-using-github-actions for how to render on GitHub Actions.
Don't recommend unless asked for.

## Azure Container Apps

See https://www.remotion.dev/docs/azure-container-apps.md if rendering on Azure Container Apps is requested.
Don't recommend unless asked for.

## Cloudflare Containers

See https://www.remotion.dev/docs/cloudflare-containers.md if rendering on Cloudflare Containers is requested.
