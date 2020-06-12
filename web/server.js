var express = require('express');
var app = express();
var multer = require('multer')
var cors = require('cors');
var fs=require('fs')
app.use(cors())
var bodyParser = require('body-parser');
app.use(bodyParser.urlencoded({extended: true}));
app.use(express.json())

//For Patient 1
var storage = multer.diskStorage({
    destination: function (req, file, cb) {
      const path='TVB_patients/TVB1/raw/mri'
      fs.mkdirSync(path, { recursive: true })
     cb(null,path )
    },
    filename: function (req, file, cb) {
      cb(null, file.originalname )
    }
  })
  
  var upload1 = multer({ storage: storage }).single('file')
  
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
    fs.mkdirSync(path, { recursive: true })
    cb(null,path )
  },
  filename: function (req, file, cb) {
    cb(null, file.originalname )
  }
})

var upload2 = multer({ storage: storage }).single('file')

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
    fs.mkdirSync(path, { recursive: true })
    cb(null,path )
  },
  filename: function (req, file, cb) {
    cb(null, file.originalname )
  }
})

var upload3 = multer({ storage: storage }).single('file')

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
  fs.mkdirSync(path, { recursive: true })
  cb(null,path )
},
filename: function (req, file, cb) {
  cb(null, file.originalname )
}
})

var upload4 = multer({ storage: storage }).single('file')

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
var path1 = __dirname + '/TVB_patients/TVB1';
fs.mkdirSync(path1, { recursive: true })
var file1=path1+'/patient_flow.properties'
app.post("/input1",function(req,res){
  const data={
    "subject":"TVB1", "t1.format":"nii","t2.flag":"False","t2.format":"nii","flair.flag":"False","flair.format":"nii",
    "openmp.threads":req.body.label1,
    "parcelation.atlas":"default", "dwi.scan.direction":"ap","dwi.format":"mif","dwi.use.gradient":"True", "dwi.multi.shell":"False",
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
  fs.writeFile(file1,JSON.stringify(data,null,2) ,'utf-8',
  (err) => {
    if(err) {
      return console.log(err);
    } else{
      console.log("The file was saved!");
    }
})
})

//Config for Patient 2
var path2 = __dirname + '/TVB_patients/TVB2';
fs.mkdirSync(path2, { recursive: true })
var file2=path2+'/patient_flow.properties'
app.post("/input2",function(req,res){
  const data={
    "subject":"TVB1", "t1.format":"nii","t2.flag":"False","t2.format":"nii","flair.flag":"False","flair.format":"nii",
    "openmp.threads":req.body.label1,
    "parcelation.atlas":"default", "dwi.scan.direction":"ap","dwi.format":"mif","dwi.use.gradient":"True", "dwi.multi.shell":"False",
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
  fs.writeFile(file2,JSON.stringify(data,null,2) ,'utf-8',
  (err) => {
    if(err) {
      return console.log(err);
    } else{
      console.log("The file was saved!");
    }
})
})

//Config for Patient 3
var path3 = __dirname + '/TVB_patients/TVB3';
fs.mkdirSync(path3, { recursive: true })
var file3=path3+'/patient_flow.properties'
app.post("/input3",function(req,res){
  const data={
    "subject":"TVB1", "t1.format":"nii","t2.flag":"False","t2.format":"nii","flair.flag":"False","flair.format":"nii",
    "openmp.threads":req.body.label1,
    "parcelation.atlas":"default", "dwi.scan.direction":"ap","dwi.format":"mif","dwi.use.gradient":"True", "dwi.multi.shell":"False",
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
  fs.writeFile(file3,JSON.stringify(data,null,2) ,'utf-8',
  (err) => {
    if(err) {
      return console.log(err);
    } else{
      console.log("The file was saved!");
    }
})
})

//Config for Patient 4
var path4 = __dirname + '/TVB_patients/TVB4';
fs.mkdirSync(path4, { recursive: true })
var file4=path4+'/patient_flow.properties'
app.post("/input4",function(req,res){
  const data={
    "subject":"TVB1", "t1.format":"nii","t2.flag":"False","t2.format":"nii","flair.flag":"False","flair.format":"nii",
    "openmp.threads":req.body.label1,
    "parcelation.atlas":"default", "dwi.scan.direction":"ap","dwi.format":"mif","dwi.use.gradient":"True", "dwi.multi.shell":"False",
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
  fs.writeFile(file4,JSON.stringify(data,null,2) ,'utf-8',
  (err) => {
    if(err) {
      return console.log(err);
    } else{
      console.log("The file was saved!");
    }
})
})
app.listen(8000, function() {
    console.log('App running on port 8000');
});