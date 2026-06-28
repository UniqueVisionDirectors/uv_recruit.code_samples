FROM node:22-slim
WORKDIR /docs
COPY package*.json ./
RUN npm ci
COPY . .
CMD ["npm", "run", "docs:dev"]
