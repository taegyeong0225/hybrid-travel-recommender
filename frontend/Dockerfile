# Stage 1: Build the React application
FROM node:16-alpine as builder

WORKDIR /app

COPY package.json ./
# Use npm ci for cleaner installs if package-lock.json is present
RUN npm install

COPY public ./public
COPY src ./src

RUN npm run build

# Stage 2: Serve the built application from a lightweight web server
FROM nginx:stable-alpine

# Copy the custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built files from the builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Expose port 80 (default for nginx)
EXPOSE 80

# Start nginx when the container launches
CMD ["nginx", "-g", "daemon off;"]