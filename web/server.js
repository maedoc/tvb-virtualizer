var express = require('express');
var app = express();
var multer = require('multer')
var cors = require('cors');
app.use(cors())


//For Patient 1
var storage = multer.diskStorage({
    destination: function (req, file, cb) {
      cb(null, 'TVB_patients/TVB1/raw/mri')
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
    cb(null, 'TVB_patients/TVB2/raw/mri')
  },
  filename: function (req, file, cb) {
    cb(null, file.originalname )
  }
})

var upload2 = multer({ storage: storage }).single('file')

app.get('/',function(req,res){
  return res.send('Hello Server')
})
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
    cb(null, 'TVB_patients/TVB3/raw/mri')
  },
  filename: function (req, file, cb) {
    cb(null, file.originalname )
  }
})

var upload3 = multer({ storage: storage }).single('file')

app.get('/',function(req,res){
  return res.send('Hello Server')
})
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
  cb(null, 'TVB_patients/TVB4/raw/mri')
},
filename: function (req, file, cb) {
  cb(null, file.originalname )
}
})

var upload4 = multer({ storage: storage }).single('file')

app.get('/',function(req,res){
return res.send('Hello Server')
})
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

app.listen(8000, function() {
    console.log('App running on port 8000');
});