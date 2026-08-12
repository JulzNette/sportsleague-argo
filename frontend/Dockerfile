FROM node:22-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

# Dev server, matching `npm run dev`; good enough for a module demo.
# For a real prod deploy, switch to `npm run build` + nginx serving /dist.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
