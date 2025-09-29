FROM node:lts-alpine3.19

WORKDIR /app

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=8000

COPY package.json ./
COPY package-lock.json ./

RUN npm ci --omit=dev

COPY . .

CMD [ "node", "app.js" ]
