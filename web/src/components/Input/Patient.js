import React, { Component } from 'react';
import Patient1 from './Patient1/InputFiles';
import Patient2 from './Patient2/InputFiles';
import Patient3 from './Patient3/InputFiles';
import Patient4 from './Patient4/InputFiles';
import Header from '../Home/Header/Header'
import Slider from "react-slick";
import "slick-carousel/slick/slick.css"; 
import "slick-carousel/slick/slick-theme.css";
import ProcessType from './ProcessType/ProcessType';

class Patient extends Component{
    render(){
        const settings = {
            dots: true,
            infinite: true,
            speed: 1500,
            slidesToShow: 1,
            slidesToScroll: 1
          };
        return(
            <div>
                <Header/>
                <Slider {...settings}>
                <Patient1/>
                <Patient2/>
                <Patient3/>
                <Patient4/>
                </Slider>
                <ProcessType/>
            </div>
        )
    }
}
export default Patient;