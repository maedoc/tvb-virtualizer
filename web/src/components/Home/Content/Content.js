import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import Paper from '@material-ui/core/Paper';
import Grid from '@material-ui/core/Grid';
import img1 from '../image/img1.jpeg';
const useStyles = makeStyles((theme) => ({
  root: {
    flexGrow: 1,
  
  },
  paper: {
    padding: theme.spacing(2),
    textAlign: 'center',
    color: theme.palette.text.primary,
  },
  img:{
    width:'100%',
    height:'100%'
  },
  detail:{
      fontSize:'28px',
      
      
  }
}));

export default function CenteredGrid() {
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <Grid container spacing={3}>
        <Grid item sm={6} md={6} lg={6}>
          <Paper className={classes.paper}>
          <img className={classes.img} alt="complex" src={img1} />

          </Paper>
        </Grid>
        <Grid item sm={6} md={6} lg={6}>
          <Paper className={classes.paper}><p className={classes.detail}>A real brain can turn to a virtual brain in 3 steps. First, the patient goes to a RMN scanner, then, the measured images go through a reconstruction pipeline, 
          and finally, the results are uploaded in TVB.
          <br/> This reconstruction pipeline is a mandatory tool,
           it takes RMN images, processes them and extracts the brain’s connectivity, 
           geometry, parcellations and other data necessary for virtualization. It produces 
           files that are compatible with TVB.<br/> So, Let's Try by uploading the input files!!!</p> </Paper>
        </Grid>
        
      </Grid>
    </div>
  );
}
