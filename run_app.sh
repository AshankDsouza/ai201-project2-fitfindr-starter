# stop the existing flask container if it's running:
docker stop fitfindr-flask || true

# delete existing flask image
docker rmi fitfindr-flask || true

# build the flask container:
docker build -t fitfindr-flask .

# run the flask container:
docker run -d -p 3000:3000 --name fitfindr-flask fitfindr-flask


# run the frontend server:

# 1. cd into the frontend directory
cd web
npm install
npm run dev




