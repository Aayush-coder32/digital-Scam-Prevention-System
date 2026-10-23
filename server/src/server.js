import 'dotenv/config';
const dns = require("node:dns/promises");
dns.setServers(["1.1.1.1","8.8.8.8"]);
import app from './app.js';
import mongoose from 'mongoose';
const port=Number(process.env.PORT||5000);
if(process.env.MONGODB_URI){mongoose.connect(process.env.MONGODB_URI).then(()=>console.log('MongoDB connected')).catch(e=>console.error('MongoDB connection failed:',e.message));}
app.listen(port,()=>console.log(`DSPS API listening on ${port}`));
