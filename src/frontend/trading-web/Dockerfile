# Estágio de build
FROM node:18-alpine as build

WORKDIR /app

# Copia arquivos de dependências
COPY src/frontend/trading-web/package*.json ./

# Instala dependências
RUN npm install

# Copia o código fonte
COPY src/frontend/trading-web/ ./

# Build da aplicação
RUN npm run build

# Estágio de produção
FROM nginx:alpine

# Copia os arquivos de build
COPY --from=build /app/build /usr/share/nginx/html

# Copia configuração do nginx
COPY src/frontend/trading-web/nginx.conf /etc/nginx/conf.d/default.conf

# Expõe a porta 3000
EXPOSE 3000

# Inicia o nginx
CMD ["nginx", "-g", "daemon off;"] 