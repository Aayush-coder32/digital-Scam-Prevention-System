import 'dotenv/config';
import dns from 'node:dns/promises';
import app from './app.js';
import mongoose from 'mongoose';

// Use public DNS resolvers for MongoDB Atlas SRV/TXT discovery.
dns.setServers(['1.1.1.1', '8.8.8.8']);
mongoose.set('autoCreate', true);
const port=Number(process.env.PORT||5000);
const mongoUri=process.env.MONGODB_URI;
const isProduction=process.env.NODE_ENV==='production';

if(isProduction&&!process.env.JWT_ACCESS_SECRET){
  throw new Error('JWT_ACCESS_SECRET must be configured before starting in production.');
}

if(mongoUri){
  mongoose.connect(mongoUri,{serverSelectionTimeoutMS:10000})
    .then(()=>console.log('MongoDB connected'))
    .catch(e=>console.error('MongoDB connection failed:',e.message));
}else{
  console.warn('MONGODB_URI is not set. Scanning works without persistence; account and history features are unavailable.');
}

const server = app.listen(port,()=>console.log(`DSPS API listening on ${port}`));

server.on('error',(error)=>{
  if(error.code==='EADDRINUSE'){
    console.error(`Port ${port} is already in use. Stop the other API process or set PORT to a different value.`);
  }else{
    console.error('API server failed to start:',error);
  }
  process.exitCode=1;
});

const shutdown=async(signal)=>{
  server.close(async()=>{
    await mongoose.disconnect().catch((error)=>console.error('MongoDB shutdown failed:',error.message));
    process.exit(0);
  });

  setTimeout(()=>{
    console.error(`Forced shutdown after receiving ${signal}.`);
    process.exit(1);
  },5000).unref();
};

process.once('SIGINT',()=>shutdown('SIGINT'));
process.once('SIGTERM',()=>shutdown('SIGTERM'));
