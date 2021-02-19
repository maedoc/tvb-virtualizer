import React, { Component } from 'react';
import InputFiles from './InputFiles';
import Header from '../Home/Header/Header'
import Slider from "react-slick";
import "slick-carousel/slick/slick.css"; 
import "slick-carousel/slick/slick-theme.css";
import ProcessType from './ProcessType/ProcessType';

class Input extends Component{
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
                <InputFiles no="1"/>
                <InputFiles no="2"/>
                <InputFiles no="3"/>
                <InputFiles no="4"/>
                </Slider>
                <ProcessType/>
            </div>
        )
    }
}
export default Input;