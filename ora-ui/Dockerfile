
# 1. Base Image
FROM node:18-alpine

# 2. Workdir
WORKDIR /app

# 3. Dependencies
COPY package*.json ./
RUN npm ci

# 4. Source
COPY . .

# 5. Build (Next.js)
RUN npm run build

# 6. Expose Port
EXPOSE 3333

# 7. Start (Production Mode)
CMD ["npm", "start", "--", "-p", "3333"]
