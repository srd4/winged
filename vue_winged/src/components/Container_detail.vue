<template>
<div class="items-container">
    <div class="filters">
            <label for="actionables">actionables</label>
            <input v-model="seeActionables" type="checkbox" name="actionables">
            
            <label for="done">done</label>
            <input v-model="seeDone" type="checkbox" name="done">

            <label for="spectrums">By spectrum</label>
            <select v-model="spectrumId" id="spectrums" name="spectrumsList">
                <option :value="null">None</option>
                <option v-if="container_spectrums" v-for="spectrum in container_spectrums" :value="spectrum.id">{{spectrum.name}}</option>
            </select>

            <input v-model="searchQuery" placeholder="Search...">

            <button v-on:click="filterItems();updateContainer(container);getContainerItems()">filter</button>
            
            <a @click="logout">Logout</a>
            <div>
                <button v-on:click="gptCurate('user_input');">User-Curate</button>
            </div>

            <div v-if="!showAiCurationConfirmation">
                <button  v-on:click="fetchComputedAiCurationCost()">AI-Curate</button>
            </div>

            <div v-if="showAiCurationConfirmation">
                <p>Estimated Cost: ${{ computedAiCurationCost }} USD</p>
                <button>Confirm AI-Curation</button>
                <button v-on:click="showAiCurationConfirmation = !showAiCurationConfirmation">Cancel</button>
            </div>
    </div>

    <div class="actions">
        <label for="spectrums">add spectrum</label>
        <select v-model="spectrumToAdd" name="spectrumsList">
            <option :value="null">None</option>
            <option v-if="available_spectrums"
            v-for="spectrum in available_spectrums"
            :value="spectrum"
            >{{spectrum.name}}</option>
        </select>
        
        <button v-on:click="addSpectrumToContainerItems(spectrumToAdd)">add spectrum</button>
            
        
    </div>

    <div>
        <!--Button to run startReclassify() on this.container.-->
        <button v-on:click="startReclassifyActionables()">Separate actions</button>
    </div>

    <ul class="item-list">            
        <li v-for="(item, index) in item_list">
            <input type="checkbox"
            v-model="item.done"
            v-on:click="toggleDone(item)">

            <span
            contenteditable="true"
            @input="handleInput"
            tabindex="0"
            :ref="'itemComponents' + index"
            v-on:keydown.enter.prevent="startNewRightBelow($event, index)"
            @blur="updateOrCreate(item, $event, index)"
            :class="{'done': item.done}"
            :key="index">
            {{item.statement}}
            </span>

            <button class="ellipsis"
            @click="toggleDropdown(index);
            ">&#8230;</button>
            
            <div style="position: relative;"
            :class="'dropdown ' + index" ref="myDiv"
            v-show="dropdownVisible === index">
                <ul class="dropdown options">

                    <li class="options option"
                    v-on:mouseover="overOption"
                    v-on:mouseleave="leaveOption"
                    v-on:click="changeActionable($event, item);toggleDropdown(index);"
                    >make {{notSeeing}}</li>

                    <li class="options option"
                    v-on:mouseover="overOption"
                    v-on:mouseleave="leaveOption"
                    >
                    <select v-model="containerToMoveTo" id="spectrums" name="spectrumsList" v-on:change="moveToContainer($event, item);toggleDropdown(index);">
                        <option :value="null">move to</option>
                        <option v-for="container in containers" :value="container.id">{{container.name}}</option>
                    </select>
                    </li>

                    <li class="options option"
                    v-on:mouseover="overOption"
                    v-on:mouseleave="leaveOption"
                    v-on:click="archiveItem(item);changeActionable($event, item);toggleDropdown(index);"
                    >archive</li>

                    <li class="options option"
                    v-on:mouseover="overOption"
                    v-on:mouseleave="leaveOption"
                    v-on:click="newSpectrumOptionsVisible === index? newSpectrumOptionsVisible = null: newSpectrumOptionsVisible = index"
                    >add spectrum </li>

                    <li class="options option"
                    v-on:mouseover="overOption"
                    v-on:mouseleave="leaveOption"
                    v-on:click="spectrumRangesVisible === index? spectrumRangesVisible = null: spectrumRangesVisible = index"
                    >spectrum ranges</li>

                        <div :class="'dropdown options ranges'"
                        v-show="true">
                            <!--v-show="item.spectrum_values && item.spectrum_values.length > 0 && spectrumRangesVisible === index">-->
                            <ul class="dropdown options ranges">
                                <li class="options option"
                                v-for="spectrum_value in item.spectrum_values">

                                    <label
                                    style="display: block;"
                                    :style="{color: spectrum_value.gpt_curated ? 'gray' : '' }"
                                    for="range">
                                    
                                        {{spectrum_value.label}}: {{spectrum_value.value}}
                                    </label>

                                    <input
                                    type="range" min="0" max="100"
                                    v-on:input="spectrum_value.value = $event.target.value"
                                    :value="spectrum_value.value"
                                    @focusout="updateSpectrum(spectrum_value)">
                                </li>
                            </ul>
                        </div>

                        <div :class="'dropdown spectrums'"
                            v-show="newSpectrumOptionsVisible === index">
                            <ul class="dropdown options">
                                <li class="options option"
                                v-for="spectrum in available_spectrums"
                                v-on:mouseover="overOption"
                                v-on:mouseleave="leaveOption"
                                v-on:click="createSpectrumValue(item, spectrum);toggleDropdown(index);"
                                >{{spectrum.name}}</li>
                            </ul>
                        </div>
                </ul>

            </div>
        </li>
    </ul>
</div>
</template>
  
<script>
import axiosAuthentication from '../axiosAuthentication';
import axiosInstance  from '../axiosInstance';

export default {
    name:'Items',
    props:{
        container : null,
    },
    data(){
        return {
            searchQuery : '',
            //list of items fetched on get request (the container's items on db).
            container_items : [],
            seeActionables : true,
            seeDone : false,
            //list of items displayed.
            seeArchived : false,
            item_list: [],
            maxLength: 2**7,
            confirming_delete: false,
            dropdownVisible : null,
            spectrumId: null,
            container_spectrums: [],
            available_spectrums: [],
            newSpectrumOptionsVisible: null,
            spectrumRangesVisible: null,
            spectrumToAdd: null,
            containerToMoveTo: null,
            containers: [],
            firstContainerId: null,
            secondContainerId: null,
            showAiCurationConfirmation: false,
            computedAiCurationCost: null,
        }
    },
    watch: {
        container() {
            this.getContainerItems();
            this.seeActionables = this.container.is_on_actionables_tab;
            this.container_spectrums = this.container.spectrum_types;
            this.available_spectrums = this.getSpectrumTypes()
            this.filterItems()
            this.getAllContainers()
        },
    },
    computed : {
        notSeeing(){return this.seeActionables? 'non-actionable':'actionable'},
    },
    methods : {
        logout(event, item) {
            axiosAuthentication.logout();
            window.location.reload();
        },
        moveToContainer(event, item){
            if (this.containerToMoveTo){
                this.updateItem(item, {parent_container: this.containerToMoveTo})
                this.containerToMoveTo = null;
            }
        },
        getAllContainers(){
            axiosInstance
                .get('/containers/')
                .then(response => {
                this.containers  = response.data
                })
        },
        addSpectrumToContainerItems(spectrum_type){
            for(let i = 0; i < this.item_list.length; i++){
                this.createSpectrumValue(this.item_list[i], spectrum_type);
                //console.log(this.item_list[i], spectrum_type)
                }
        },
        getSpectrumTypes(){
            axiosInstance.get(`/spectrum_type/`)
            .then(response => {
                //get container items original list.
                this.available_spectrums = response.data;
            })
            .catch(error => {
                console.log("Problem on updating containers w/ getContainerItems method", error)
            })
        },
        createSpectrumValue(item, spectrum){
            const data = {
                'value':0,
                'spectrum_type':spectrum.id,
                'parent_item': item.id,
            }
            axiosInstance.post('/spectrum_value/', data, {
                partial: true
                })
                .then(response => {
                item.spectrum_values? item.spectrum_values.push(response.data) : item.spectrum_values = [];
                console.log('spectrum_value created.');
                })
                .catch(error => {
                console.error('Error creating spectrum_value:', error)
                })
        },
        updateSpectrum(spectrum_value){
            //console.log(spectrum_value)
            axiosInstance.put('/spectrum_value/'+ String(spectrum_value.id)+'/', spectrum_value, {
                partial: true
                })
                .then(response => {
                console.log('Spectrum updated.');
                })
                .catch(error => {
                console.error('Error updating spectrum:', error)
                })
        },
        sortBySpectrum(){
            this.item_list.sort(this.compareItemsOnSpectrum);
        },
        spectrumValue(item){
            if(item.spectrum_values){
                for(let i = 0; i < item.spectrum_values.length; i++){
                    if(
                        item.spectrum_values &&
                        item.spectrum_values[i] &&
                        item.spectrum_values[i].spectrum_type == this.spectrumId
                    ){
                        return item.spectrum_values[i].value;
                    }
                }
            }
            return null;
        },
        compareItemsOnSpectrum( item_1, item_2 ) {
            if(this.spectrumValue(item_1) && this.spectrumValue(item_2)){
                const a = this.spectrumValue(item_1);
                const b = this.spectrumValue(item_2);
                if ( a < b ){
                    return 1;
                } else if ( a > b ){
                    return -1;
                }else {

                    return 0;
                }
            }
            else {
                if(!this.spectrumValue(item_1) && !this.spectrumValue(item_2)){
                    return 0;
                }else if(!this.spectrumValue(item_1) && this.spectrumValue(item_2)){
                    return 1;
                }else if(this.spectrumValue(item_1) && !this.spectrumValue(item_2)){
                    return -1;
                }
            }
        },
        changeActionable(event, item){
            item.actionable = !item.actionable;
            this.updateItem(item, item);
        },
        leaveOption(event){
            event.target.classList.remove('active-option')  
        },
        overOption(event){
            event.target.classList.add('active-option')
        },
        fuck(){
            console.log("fuck");
        },
        toggleDropdown(index){
            if(this.dropdownVisible === index){
                this.dropdownVisible = null;
            }else{
                this.dropdownVisible = index;
                window.addEventListener('click', this.toggleDiv, true);
            }
        },
        toggleDiv(event) {
            const div = this.$refs.myDiv[this.dropdownVisible];
            if (div && !div.contains(event.target)) {
                window.removeEventListener('click', this.toggleDiv, false);
                this.dropdownVisible = null;
                //this.spectrumRangesVisible = null;
                this.newSpectrumOptionsVisible = null;
            }
            
        },
        archiveItem(item){
            item.archived = !item.archived;
            this.updateItem(item, item);
        },
        handleInput(event) {
            const text = event.target.innerText;
            if (text.length > this.maxLength) {
                event.target.classList.add('danger')
            }else{
                event.target.classList.remove('danger')
            }
        },
        filterItems(){
            this.item_list = this.container_items.filter(item =>{
            return item.statement.toLowerCase().includes(this.searchQuery.toLowerCase()) &&
            item.actionable == this.seeActionables &&
            item.done == this.seeDone &&
            item.archived == this.seeArchived //supposed to be false at all times.
            }
            );
        },
        //updateContainerItems() {
        //    this.container_items = this.getContainerItems(this.container);
        //},
        getContainerItems() {
            axiosInstance.get(`/containers/${this.container.id}/items/`)
            .then(response => {
                //get container items original list.
                this.container_items = response.data;
                //get items to display ready.
                this.item_list = this.container_items.slice();

                //filter item_list by current container state.
                this.filterItems()

                this.sortBySpectrum()
            })
            .catch(error => {
                console.log("Problem on updating containers w/ getContainerItems method", error)
            })
        },
        startNewRightBelow(event, index) {
            if (event.target.textContent.length > this.maxLength){
                this.focusElement(index);
                event.target.classList.add('danger');
                return;
            } else if (event.target.textContent.length === 0 && this.item_list[index].id == null){
                this.item_list.splice(index, 1)
                return;
            }

            const { target } = event;
            const selection = window.getSelection();
            const startOffset = selection.anchorOffset;
            const endOffset = selection.focusOffset;
            const text = target.textContent;

            const oldText = text.slice(0, Math.min(startOffset, endOffset));
            const newText = text.slice(Math.max(startOffset, endOffset));

            target.textContent = oldText;
            
            this.$nextTick(() => {
                this.addItem(newText, index + 1);
                });
            },
        addItem(statement, index) {
            const newItem = {
                done: this.seeDone,
                actionable : this.seeActionables,
                statement: statement,
                id: null,

                }

            if (index === this.item_list.length) {
                this.item_list.push(newItem);
            } else {
                this.item_list.splice(index, 0, newItem);
            }

            this.$nextTick(() => {
                    this.focusElement(index);
                });

        },
        focusElement(index) {
            const element = this.$refs['itemComponents' + index];
            if (element[0]) {
                //console.log(element[0])
                element[0].focus();
            }
        },
        updateOrCreate(item, event, index){
            if (event.target.textContent.length > this.maxLength){
                //remove empty contenteditable from container_items.
                this.focusElement(index);
                event.target.classList.add('danger');
                return;
            }else if (event.target.textContent.length === 0 && item.id === null){
                this.item_list.splice(index, 1)
                return;
            }

            if(item.id && item.statement != event.target.textContent){
                item.statement = event.target.textContent
                this.updateItem(item, {'statement':item.statement});
            }
            else if(item.id == null){
                item.statement = event.target.textContent
                this.createItem(item, {
                    'statement' : item.statement,
                    'parent_container':this.container.id,
                    'actionable':this.seeActionables,
                });
            }
        },
        updateItem(item, newData){
            //send put request to update item.
            //console.log(newData)
            //console.log(item)
            axiosInstance.put('/items/'+ String(item.id)+'/', newData, {
                partial: true
                })
                .then(response => {
                console.log('Item updated.');
                })
                .catch(error => {
                console.error('Error updating item:', error)
                })
        },
        createItem(item, data){
            //sends post to create new element.
            axiosInstance.post('/items/', data, {
                partial: true
                })
                .then(response => {
                item.id = response.data.id;
                console.log('Item created.');
                })
                .catch(error => {
                console.error('Error creating item:', error)
                })
        },
        toggleDone(item){
            if(item.id){
                item.done = !item.done;
                this.updateItem(item, item);
            }
        },
        updateContainer(container) {
            if(this.container.is_on_actionables_tab != this.seeActionables){
                this.container.is_on_actionables_tab = this.seeActionables;
                axiosInstance.put('/containers/'+ String(this.container.id)+'/', container, {
                partial: true
                })
                .then(response => {
                //console.log('Container updated:',  response.data)
                })
                .catch(error => {
                console.error('Error updating container:', error)
                })
            }
        },
        gptCurate(comparisonMode){
            let link = '/containers/' + String(this.container.id) + "/run-script/spectrumtypes/" + String(this.spectrumId) + "/" + comparisonMode + "/";
            axiosInstance.get(link)
                .then(response => {
                    console.log(response.data.message);
                })
                .catch(error => {
                    console.error('Error gpt-curating', error);
                });
        },
        startReclassify() {
            if (!this.firstContainerId || !this.secondContainerId) {
                console.error("Both containers must be selected");
                return;
            }

            let link = `/containers/${String(this.container.id)}/reclassify/${String(this.firstContainerId)}/${String(this.secondContainerId)}/`;

            axiosInstance.get(link)
                .then(response => {
                    console.log(response.data.message); // Handle your response here
                })
                .catch(error => {
                    console.error('Error initiating reclassification:', error);
                });
        },
        startReclassifyActionables() {
            let link = `/containers/${String(this.container.id)}/reclassify-actionable/`;

            axiosInstance.post(link)
                .then(response => {
                    console.log(response.data.message);
                })
                .catch(error => {
                    console.error('Error initiating reclassification:', error);
                });
        },
        fetchComputedAiCurationCost(){
            let link = `/containers/${String(this.container.id)}/spectrumtypes/${String(this.spectrumId)}/items-vs-spectrum-comparison-cost/`

            axiosInstance.get(link)
                .then(response =>{
                    this.computedAiCurationCost = Math.round(response.data.cost * 100) /100
                    this.showAiCurationConfirmation = !this.showAiCurationConfirmation
                    console.log(response.data.cost)
                })
                .catch(error => {
                    console.error('Error fetching cumputed ai curation cost:', error);
                });
        }
    },
}
</script>


<style>
.items-container {
    background-color: #131415;
    color: #e3e3e3;
    flex: 4;
    width: 80%;
}

.done {
    text-decoration-line:line-through;
}

.item-list {
    padding-left: 0;
}

.done-button{
    display: inline;
    margin-right: 0.25rem;
    cursor: pointer;
}

.danger {
    outline: 1px solid red;
}

span {
    outline: 0px solid transparent;
}

.delete {
    background-color: transparent;
    outline: none;
    border: none;
    color: red;
    cursor: pointer;
}

.ellipsis {
    background-color: transparent;
    outline: none;
    border: none;
    color: gray;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 900;
}

.dropdown {
    display: inline-block;
    background-color: #161718;
    color: #e3e3e3;
    border: gray solid 1px;
}

.dropdown.options {
    position: absolute;
    top: 50%;
    left: auto;
    right: 100%;
    width: max-content;
    padding: 0;
}

.dropdown.spectrums {
    position: absolute;
    top: 50%;
    left: auto;
    right: 100%;
    width: max-content;
    padding: 0;
}

.options{
    display: block;
    cursor: pointer;
}

.active-option {
    background-color: #e3e3e3;
    color: #131415;
}


@media screen and (max-width: 768px) {
  .dropdown.spectrums,  .dropdown.options{
    left: auto;
    right: 0;
  }
}

</style>
