# Independent witness service (H2A reference · ADR-005 / L3). Co-signs an implementer's audit-chain
# head from its OWN trust domain. Zero runtime deps; tsx-at-runtime. Build context = this directory.
#
# NOTE: only needed once L3 anchoring is turned on (Bridle WITNESS_URL points here). Not part of the
# initial interim-L2 hosted demo. Set WITNESS_SIGNING_KEY (PKCS8 PEM) for a durable pubkey; else it
# generates an ephemeral key per process.
FROM node:22-slim
WORKDIR /svc

# tsx is a devDependency and IS the runtime (npm start → tsx src/service.ts) — keep devDeps installed.
COPY package.json package-lock.json tsconfig.json ./
COPY src ./src
RUN npm ci

ENV PORT=8791
EXPOSE 8791
CMD ["npm", "start"]
