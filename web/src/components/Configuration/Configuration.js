import React, { Component } from 'react';
import Header from '../Home/Header/Header';
import InputConfiguration from './InputConfiguration'
import Slider from "react-slick";
import "slick-carousel/slick/slick.css"; 
import "slick-carousel/slick/slick-theme.css";
import './Configuration.css';
import axios from 'axios'
class Configuration extends Component{
    handleClick=()=>{
           alert("Docker started on server")
           axios.post('http://localhost:8000/start')
         
         }
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
                <InputConfiguration no="1"/>
                <InputConfiguration no="2"/>
                <InputConfiguration no="3"/>
                <InputConfiguration no="4"/>
                </Slider>
                <button className="proceed_btn" onClick={this.handleClick}>Start the Docker Container</button>


            </div>
            
        )
    }
}
export default Configuration;