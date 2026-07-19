# Issuer / status service — the interim fiduciary + revocation authority (H2A reference).
# Zero runtime deps; runs the TypeScript source directly via tsx. Build context = this directory.
#
# For a HOSTED deployment set durable custody (else key/list-id regenerate per restart — see
# ../../../bridle/deploy/RUNBOOK.md §1): ISSUER_SIGNING_KEY (PKCS8 PEM), ISSUER_LIST_ID, ISSUER_ISS,
# FIDUCIARY_TOKEN (gates /sign-grant + /revoke), and optionally ISSUER_REVOKED_PATH on a volume.
FROM node:22-slim
WORKDIR /svc

# Manifests first for layer caching. `npm ci` installs devDeps too — tsx is a devDependency and is the
# runtime (npm start → tsx src/service.ts), so do NOT set NODE_ENV=production / --omit=dev before this.
COPY package.json package-lock.json tsconfig.json ./
COPY src ./src
RUN npm ci

ENV PORT=8790
EXPOSE 8790
CMD ["npm", "start"]
