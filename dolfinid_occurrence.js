var __occurrence__sequence = 0;

class dolfin_occurrence_cluster {
    constructor() {
        this.occurrence_hash = {};
    }
    add_occurrence(a_occ){

    }
}
// First, checks if it isn't implemented yet.
if (!String.prototype.format) {
    String.prototype.format = function() {
      var args = arguments;
      return this.replace(/{(\d+)}/g, function(match, number) { 
        return typeof args[number] != 'undefined'
          ? args[number]
          : match
        ;
      });
    };
 }

class dolfin_occurrence {
    constructor(id,latitude, longitude) {
        this.id = id;
        this.location_key = latitude + '_' + longitude;
        this.latitude = latitude;
        this.longitude = longitude;
        this.occurrence_data = {};
        this.occurrence_list = [];
        this.image_data_hash = {};
        this.finid_list = [];
        this.display_hash = {};
        this.display_row = 0;
        this.visible = true;
        this.position  = new kakao.maps.LatLng(this.latitude, this.longitude);
        this.marker_instance = new kakao.maps.Marker({position: this.position});
        this.custom_overlay_instance = new kakao.maps.CustomOverlay({position: this.position, xAnchor:0.5,yAnchor:3.5, content:'<div>' + this.id + '</div>'});
        //this.custom_overlay_instance.setMap()
        this.overlay_instance = new kakao.maps.CustomOverlay({'position': this.position,'marker': this.marker_instance,'content': ''});
        //this.break_point_label = '';
        this.iw_content = '<div style="padding:5px;"></div>';
        this.iw_position = this.position;
        this.infowindow_instance = new kakao.maps.InfoWindow({'position' : this.position, 'content' : this.div_instance, 'removable' : true});
        this.parent = null;
        this.children = [];
        this.cluster_max_show = 5;
        this.map = null;
        this.div_content = '';
        this.sticky = false;
    }
    add_children(a_occ){
        this.children[this.children.length] = a_occ;
        //console.log( "add children:", this.id, a_occ.id, " children count:", this.children.length);
    }
    calculate_distance(a_occ){
        dist = this.distance(this.latitude, this.longitude, a_occ.latitude, a_occ.longitude);
        return dist;
    }
    get_marker(){
        return this.marker_instance;
    }
    set_map(map){
        this.marker_instance.setMap(map);
        this.custom_overlay_instance.setMap(map);
        //console.log(this.custom_overlay_instance);
        this.map = map;
    }
    show_infowindow(){
        //this.infowindow_instance.setContent(this.div_content);
        this.infowindow_instance.open(this.map, this.marker_instance);
        //this.infowindow_instance.setMap(this.map);
        this.custom_overlay_instance.setMap(null);
    }
    hide_infowindow(){
        //this.infowindow_instance.setContent("<div>" + this.id + "</div>");
        this.infowindow_instance.setMap(null);
        this.custom_overlay_instance.setMap(this.map);
    }
    add_image_data(image_name,image_data){
        //console.log("add data", this.id, image_name)
        if(!Object.keys(this.image_data_hash).includes(image_name)){
            this.image_data_hash[image_name] = image_data;
        }
        var l_date = image_data['image_date'];
        var l_time = image_data['image_time'];
        for(var idx=0;idx<image_data['finid_list'].length;idx++){
            this.occurrence_list[this.occurrence_list.length] = [ image_name, l_date, l_time, image_data['finid_list'][idx] ];
        }
        this.custom_overlay_instance.setContent('<div style="font-size:12px; background-color: rgba(255, 255, 255, 0.6);">'+l_date+'</div>');
    }
    update_content(){
        //console.log("update_content", this.id);
        var occ_hash = {};
        var date_list = [];
        for(var idx=0;idx<this.occurrence_list.length;idx++){
            var [ l_imagename, l_date, l_time, l_finid ] = this.occurrence_list[idx];
            //console.log(l_date,l_time,l_finid);
            var occ_key = [ l_date, l_time, l_finid ].join(" ");
            if( !Object.keys(occ_hash).includes(occ_key)){
                occ_hash[occ_key] = 0;
            }
            if(!date_list.includes(l_date)){
                date_list[date_list.length] = l_date;
            }
            occ_hash[occ_key] += 1;
        }
        var occ_key_list = Object.keys(occ_hash);
        for(var idx=0;idx<occ_key_list.length;idx++){
            var occ_key = occ_key_list[idx];
            this.add_occurrence_display(occ_key, occ_hash[occ_key]);
            //console.log(occ_key, occ_hash[occ_key]);
        }
        //console.log(date_list);
        
    }
    toggle_sticky() {
        this.sticky = !this.sticky;
    }
    set_visible( visible_true ){
        if( visible_true ) {
            this.set_map(map);
        } else {
            this.set_map(null);
        }
        this.visible = visible_true;
    }
    reset_display(){
        //this.display_hash = {};
        this.div_content = document.createElement('div');
        this.div_content.style.fontSize = '12px';
        this.div_content.style.width = '200px';
        this.div_content.style.height = '20px';
        this.div_content.style.padding = '3px';
        this.display_row = 0;
        this.div_content.appendChild(document.createTextNode('#'+String(this.id)));
        this.div_content.appendChild(document.createElement('br'));
        this.infowindow_instance.setContent(this.div_content);
        //console.log(this.id,"children:", this.children.length);
    }
    add_occurrence_display( a_occ_key, a_occ_count ){
        this.div_content.appendChild(document.createTextNode("{0} ({1})".format(a_occ_key, a_occ_count)));
        this.div_content.appendChild(document.createElement('br'));
        this.display_row += 1;
        this.div_content.style.height = String( 17 * (this.display_row + 1 )) + 'px';
    }
    update_cluster_display(){
        //console.log("update cluster display", this.id, this.children.length)
        var local_div = document.createElement("div");
        //console.log("update display 1", this.id, this.children.length, local_div);
        local_div.appendChild(this.div_content);
        //console.log("update display 2", this.id, this.children.length, local_div);
        var max_len = this.children.length;
        if( max_len > this.cluster_max_show ) { max_len = this.cluster_max_show;}
        //local_div.appendChild(document.createTextNode("children"))
        for(idx=0;idx<max_len;idx++){
            local_div.appendChild(this.children[idx].div_content)
        }
        //console.log(local_div)
        if( this.children.length > this.cluster_max_show ) { 
            //console.log(this.id, "children length > 3");
            var more_div = document.createElement("div");
            more_div.style.fontSize = '12px';
            more_div.appendChild(document.createTextNode("...(+" + String( this.children.length-max_len)+")"))
            local_div.appendChild(more_div); 
        }
        //console.log("update display 3", this.id, this.children.length, this.div_content, local_div);
        //console.log("update cluster display:", this.infowindow_instance.getContent(), local_div);
        this.infowindow_instance.setContent(local_div);
        //console.log("update cluster display:", this.infowindow_instance.getContent(), local_div);
        //console.log("update display 4", this.id, this.children.length, this.div_content, local_div);
    }
    set_display(a_finid, a_date){
        //return
        //display_hash = this.display_hash;
        //console.log(this, this.display_hash);
        key_list = Object.keys(this.display_hash);
        //console.log(key_list);
        if(!(key_list.includes(a_finid))){
            this.display_hash[a_finid] = [];
        }
        if(!(this.display_hash[a_finid].includes(a_date))){
            this.display_hash[a_finid][this.display_hash[a_finid].length] = a_date;
            this.display_hash[a_finid].sort();
        }
	    var div_element = document.createElement('div');
        var finid_list = Object.keys(this.display_hash);
        var div_text_list = [];
        finid_list.sort();
        for(idx=0;idx<finid_list.length;idx++){
            var date_list = this.display_hash[finid_list[idx]];
            var date_text = date_list.join(", ");
            var tn = document.createTextNode(finid_list[idx] + "(" + date_text + ")<br/>");
            div_element.appendChild(tn);
        }
        this.div_content = div_element;
        this.infowindow_instance.setContent(div_element);
    }
    distance(lat1, lon1, lat2, lon2 ) {
        if ((lat1 == lat2) && (lon1 == lon2)) {
            return 0;
        }
        else {
            var radlat1 = Math.PI * lat1/180;
            var radlat2 = Math.PI * lat2/180;
            var theta = lon1-lon2;
            var radtheta = Math.PI * theta/180;
            var dist = Math.sin(radlat1) * Math.sin(radlat2) + Math.cos(radlat1) * Math.cos(radlat2) * Math.cos(radtheta);
            if (dist > 1) {
                dist = 1;
            }
            dist = Math.acos(dist);
            dist = dist * 180/Math.PI;
            dist = dist * 60 * 1.1515;
            dist = dist * 1.609344;
            return dist;
        }
    }
}