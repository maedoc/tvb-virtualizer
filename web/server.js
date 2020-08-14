var express = require('express');
var app = express();
var multer = require('multer')
var cors = require('cors');
var fs=require('fs')
app.use(cors())
var bodyParser = require('body-parser');
app.use(bodyParser.urlencoded({extended: true}));
app.use(express.json())
var parser = require("properties-file");
var base64 = require('base-64');
var fetch=require('node-fetch');

//For Patient 1
var storage = multer.diskStorage({
    destination: function (req, file, cb) {
      const path='TVB_patients/TVB1/raw/mri'
      if(!fs.existsSync(path)){
        fs.mkdirSync(path, { recursive: true })
      }
     cb(null,path )
    },
    filename: function (req, file, cb) {
      cb(null, file.originalname )
    }
  })
  
  var upload1 = multer({ storage: storage }).array('file')
  
app.get('/',function(req,res){
    return res.send('Hello Server')
})

app.post('/upload1',function(req, res) {
    upload1(req, res, function (err) {
     
        if (err instanceof multer.MulterError) {
            return res.status(500).json(err)
        } else if (err) {
            return res.status(500).json(err)
           } 
          return res.status(200).send(req.file)
       })
});



//For Patient 2
var storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const path='TVB_patients/TVB2/raw/mri'
    if(!fs.existsSync(path)){
      fs.mkdirSync(path, { recursive: true })
    }
      cb(null,path )
  },
  filename: function (req, file, cb) {
    cb(null, file.originalname )
  }
})

var upload2 = multer({ storage: storage }).array('file')

app.post('/upload2',function(req, res) {
  
  upload2(req, res, function (err) {
   
      if (err instanceof multer.MulterError) {
          return res.status(500).json(err)
      } else if (err) {
          return res.status(500).json(err)
        } 
      
      return res.status(200).send(req.file)
     })
});



//For Patient 3
var storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const path='TVB_patients/TVB3/raw/mri'
    if(!fs.existsSync(path)){
      fs.mkdirSync(path, { recursive: true })
    }
    cb(null,path )
  },
  filename: function (req, file, cb) {
    cb(null, file.originalname )
  }
})

var upload3 = multer({ storage: storage }).array('file')

app.post('/upload3',function(req, res) {
  
  upload3(req, res, function (err) {
   
      if (err instanceof multer.MulterError) {
          return res.status(500).json(err)
      } else if (err) {
          return res.status(500).json(err)
      } 
      
      return res.status(200).send(req.file)
    })
});



//For Patient 4
var storage = multer.diskStorage({
destination: function (req, file, cb) {
  const path='TVB_patients/TVB4/raw/mri'
  if(!fs.existsSync(path)){
    fs.mkdirSync(path, { recursive: true })
  }
    cb(null,path )
},
filename: function (req, file, cb) {
  cb(null, file.originalname )
}
})

var upload4 = multer({ storage: storage }).array('file')

app.post('/upload4',function(req, res) {

upload4(req, res, function (err) {
 
    if (err instanceof multer.MulterError) {
        return res.status(500).json(err)
    } else if (err) {
        return res.status(500).json(err)
    } 
    
    return res.status(200).send(req.file)
  })
});


//Config for Patient 1
var path1 = __dirname + '/TVB_patients/TVB1/configs';
fs.mkdirSync(path1, { recursive: true })
var file1=path1+'/patient_flow.properties'
app.post("/input1",function(req,res){
  const data={
    "subject":"TVB1", "t1.format":"nii","t2.flag":"False","t2.format":"nii","flair.flag":"False","flair.format":"nii",
    "openmp.threads":req.body.label1,
    "parcelation.atlas":req.body.label5, 
    "dwi.scan.direction":"ap","dwi.format":"mif","dwi.use.gradient":"True", "dwi.multi.shell":"False",
    "mrtrix.threads":req.body.label2,
    "dwi.is.reversed":"False",
    aseg_lh_labels:req.body.aseg_lh_labels,
    aseg_rh_labels:req.body.aseg_rh_labels,
    use_flirt:req.body.use_flirt,
    strmlns_no:req.body.strmlns_no,
    strmlns_sift_no:req.body.strmlns_sift_no,
    strmlns_len:req.body.strmlns_len,
     strmlns_step:req.body.strmlns_step,
     "ct.flag":"False","ct.format":"nii","bem.surfaces":"False","use.openmeeg":"False",
     "ct.elec.intensity.th":req.body.label3,
     "seeg.flag":"False","seeg.gain.use.dp":"False","seeg.gain.use.mrs":"False","eeg.flag":"False","meg.flag":"False","resample.flag":"False","trgsubject":"fsaverage5",
     "decim.factor":req.body.label4,
     os:"LINUX"
    }
  fs.writeFile(file1,parser.stringify(data) ,'utf-8',
  (err) => {
    if(err) {
      return console.log(err);
    }
})
})

//Config for Patient 2
var path2 = __dirname + '/TVB_patients/TVB2/configs';
fs.mkdirSync(path2, { recursive: true })
var file2=path2+'/patient_flow.properties'
app.post("/input2",function(req,res){
  const data={
    "subject":"TVB2", "t1.format":"nii","t2.flag":"False","t2.format":"nii","flair.flag":"False","flair.format":"nii",
    "openmp.threads":req.body.label1,
    "parcelation.atlas":req.body.label5, 
    "dwi.scan.direction":"ap","dwi.format":"mif","dwi.use.gradient":"True", "dwi.multi.shell":"False",
    "mrtrix.threads":req.body.label2,
    "dwi.is.reversed":"False",
    aseg_lh_labels:req.body.aseg_lh_labels,
    aseg_rh_labels:req.body.aseg_rh_labels,
    use_flirt:req.body.use_flirt,
    strmlns_no:req.body.strmlns_no,
    strmlns_sift_no:req.body.strmlns_sift_no,
    strmlns_len:req.body.strmlns_len,
     strmlns_step:req.body.strmlns_step,
     "ct.flag":"False","ct.format":"nii","bem.surfaces":"False","use.openmeeg":"False",
     "ct.elec.intensity.th":req.body.label3,
     "seeg.flag":"False","seeg.gain.use.dp":"False","seeg.gain.use.mrs":"False","eeg.flag":"False","meg.flag":"False","resample.flag":"False","trgsubject":"fsaverage5",
     "decim.factor":req.body.label4,
     os:"LINUX"
    }
  fs.writeFile(file2,parser.stringify(data) ,'utf-8',
  (err) => {
    if(err) {
      return console.log(err);
    }
})
})

//Config for Patient 3
var path3 = __dirname + '/TVB_patients/TVB3/configs';
fs.mkdirSync(path3, { recursive: true })
var file3=path3+'/patient_flow.properties'
app.post("/input3",function(req,res){
  const data={
    "subject":"TVB3", "t1.format":"nii","t2.flag":"False","t2.format":"nii","flair.flag":"False","flair.format":"nii",
    "openmp.threads":req.body.label1,
    "parcelation.atlas":req.body.label5,
    "dwi.scan.direction":"ap","dwi.format":"mif","dwi.use.gradient":"True", "dwi.multi.shell":"False",
    "mrtrix.threads":req.body.label2,
    "dwi.is.reversed":"False",
    aseg_lh_labels:req.body.aseg_lh_labels,
    aseg_rh_labels:req.body.aseg_rh_labels,
    use_flirt:req.body.use_flirt,
    strmlns_no:req.body.strmlns_no,
    strmlns_sift_no:req.body.strmlns_sift_no,
    strmlns_len:req.body.strmlns_len,
     strmlns_step:req.body.strmlns_step,
     "ct.flag":"False","ct.format":"nii","bem.surfaces":"False","use.openmeeg":"False",
     "ct.elec.intensity.th":req.body.label3,
     "seeg.flag":"False","seeg.gain.use.dp":"False","seeg.gain.use.mrs":"False","eeg.flag":"False","meg.flag":"False","resample.flag":"False","trgsubject":"fsaverage5",
     "decim.factor":req.body.label4,
     os:"LINUX"
    }
  fs.writeFile(file3,parser.stringify(data) ,'utf-8',
  (err) => {
    if(err) {
      return console.log(err);
    }
})
})

//Config for Patient 4
var path4 = __dirname + '/TVB_patients/TVB4/configs';
fs.mkdirSync(path4, { recursive: true })
var file4=path4+'/patient_flow.properties'
app.post("/input4",function(req,res){
  const data={
    "subject":"TVB4", "t1.format":"nii","t2.flag":"False","t2.format":"nii","flair.flag":"False","flair.format":"nii",
    "openmp.threads":req.body.label1,
    "parcelation.atlas":req.body.label5,
    "dwi.scan.direction":"ap","dwi.format":"mif","dwi.use.gradient":"True", "dwi.multi.shell":"False",
    "mrtrix.threads":req.body.label2,
    "dwi.is.reversed":"False",
    aseg_lh_labels:req.body.aseg_lh_labels,
    aseg_rh_labels:req.body.aseg_rh_labels,
    use_flirt:req.body.use_flirt,
    strmlns_no:req.body.strmlns_no,
    strmlns_sift_no:req.body.strmlns_sift_no,
    strmlns_len:req.body.strmlns_len,
     strmlns_step:req.body.strmlns_step,
     "ct.flag":"False","ct.format":"nii","bem.surfaces":"False","use.openmeeg":"False",
     "ct.elec.intensity.th":req.body.label3,
     "seeg.flag":"False","seeg.gain.use.dp":"False","seeg.gain.use.mrs":"False","eeg.flag":"False","meg.flag":"False","resample.flag":"False","trgsubject":"fsaverage5",
     "decim.factor":req.body.label4,
     os:"LINUX"
    }
  fs.writeFile(file4,parser.stringify(data) ,'utf-8',
  (err) => {
    if(err) {
      return console.log(err);
    }
})
})

//Monitoring Api
app.get('/auth',function(request,response){
var url = 'https://localhost:5000/api/v1/user/punit/root/';
var username = 'punit';
var password = '123';
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0" 
global.fetch = fetch
global.Headers = fetch.Headers;
var headers = new Headers();
headers.append('Authorization', 'Basic ' + base64.encode(username + ":" + password));
fetch(url, {method:'GET',
        headers: headers,
       })
       .then((res) => { 
        status = res.status; 
        return res.json() 
      })
      .then((jsonData) => {
        response.send(jsonData);
      })
      .catch((err) => {
        response.error(err);
      });
})
app.get('/auth/:wf_id',function(request,response){
  var wf_id=request.params.wf_id
  var url = 'https://localhost:5000/api/v1/user/punit/root/'+wf_id+'/workflow/1/job';
  var username = 'punit';
  var password = '123';
  process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0" 
  global.fetch = fetch
  global.Headers = fetch.Headers;
  var headers = new Headers();
  headers.append('Authorization', 'Basic ' + base64.encode(username + ":" + password));
  fetch(url, {method:'GET',
          headers: headers,
         })
         .then((res) => { 
          status = res.status; 
          return res.json() 
        })
        .then((jsonData) => {
          response.send(jsonData);
        })
        .catch((err) => {
          response.error(err);
        });
  })
app.get('/auth/:wf_id/:state',function(request,response){
  var wf_id=request.params.wf_id
  var state=request.params.state
  var url = 'https://localhost:5000/api/v1/user/punit/root/'+wf_id+'/workflow/1/job/'+state;
  var username = 'punit';
  var password = '123';
  process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0" 
  global.fetch = fetch
  global.Headers = fetch.Headers;
  var headers = new Headers();
  headers.append('Authorization', 'Basic ' + base64.encode(username + ":" + password));
  fetch(url, {method:'GET',
          headers: headers,
         })
         .then((res) => { 
          status = res.status; 
          return res.json() 
        })
        .then((jsonData) => {
          response.send(jsonData);
        })
        .catch((err) => {
          console.log("No Jobs are in the "+state+" state");
        });
  })
app.listen(8000, function() {
    console.log('App running on port 8000');
});