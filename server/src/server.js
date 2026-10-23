import 'dotenv/config';
import dns from 'node:dns/promises';
import app from './app.js';
import mongoose from 'mongoose';

// Use public DNS resolvers for MongoDB Atlas SRV/TXT discovery.
dns.setServers(['1.1.1.1', '8.8.8.8']);
mongoose.set('autoCreate', true);
const port=Number(process.env.PORT||5000);
const mongoUri=process.env.MONGODB_URI;

if(mongoUri){
  mongoose.connect(mongoUri,{serverSelectionTimeoutMS:10000})
    .then(()=>console.log('MongoDB connected'))
    .catch(e=>console.error('MongoDB connection failed:',e.message));
}else{
  console.warn('MONGODB_URI is not set. Scanning works without persistence; account and history features are unavailable.');
}

app.listen(port,()=>console.log(`DSPS API listening on ${port}`))r;
