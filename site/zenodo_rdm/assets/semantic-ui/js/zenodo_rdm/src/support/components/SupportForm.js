import { PropTypes } from "prop-types";
import React, { Component } from "react";
import { Formik, Form } from "formik";
import { Form as SemanticForm, Button, Modal } from "semantic-ui-react";
import { http, TextField, TextAreaField, ToggleField } from "react-invenio-forms";
import { remove, set } from "lodash";
import CategoryDropdown from "./CategoryDropdown";
import FileUploader from './FileUploader';

// TODO translations
// TODO implement error notification
// TODO implement recaptcha
// TODO required fields are highlighted by the component and not Formik

const requestConfig = {
    headers: {
        "Accept": "application/json",
        'Content-Type': 'multipart/form-data',
    },
};

function formikToFormData(values) {
    const formData = new FormData();
    // Append each key/value pair to formData
    Object.keys(values).forEach((key) => {
        let currentValue = values[key];
        if (Array.isArray(currentValue)) {
            currentValue.forEach((val) => {
                formData.append(key, val);
            })
        } else {
            formData.append(key, currentValue);
        }
    })

    return formData;
}


class SupportForm extends Component {

    constructor(props) {
        super(props);
    }

    deserializeFieldErrors = (errors) => {
        /**
         * Deserialises field errors from the API to be consumed by the front-end.
         * The output's format works with Formik.
         */
        let deserializedErrors = {};
        if (Array.isArray(errors)) {
            for (const e of errors) {
                if (
                    Object.prototype.hasOwnProperty.call(e, "field") &&
                    Object.prototype.hasOwnProperty.call(e, "messages")
                ) {
                    set(deserializedErrors, e.field, e.messages.join(" "));
                }
            }
        }
        return deserializedErrors;
    };

    onSubmit = async (values, formikBag) => {
        const { apiEndpoint } = this.props;
        const formData = formikToFormData(values);
        try {
            const response = await http.post(apiEndpoint, formData, requestConfig)
            window.location = response.request.responseURL;
        } catch (error) {
            let errorMessage = error.message;

            // API errors need to be deserialised to highlight fields.
            const apiResponse = error?.response?.data;
            if (apiResponse) {
                const apiErrors = apiResponse.errors || [];
                const deserializedErrors = this.deserializeFieldErrors(apiErrors);
                
                // Highlight errors using formik
                formikBag.setErrors(deserializedErrors);
                errorMessage = apiResponse.message || errorMessage;
            }

            // TODO show error notification
            console.error(errorMessage);
        }
    }


    render() {
        const {
            categories,
            name,
            isUserAuthenticated,
            userBrowser,
            userPlatform,
            userMail,
            maxFileSize
        } = this.props;

        const defaultCategory = categories.length > 0 ? categories[0].key : '';

        const initialValues = {
            email: userMail,
            name: name,
            category: defaultCategory,
            sysInfo: false,
            files: []
        }

        const sysInfo = `Browser: ${userBrowser} Operating System: ${userPlatform}`;

        return (
            <Formik
                initialValues={initialValues}
                onSubmit={this.onSubmit}
                validateOnChange={false}
                validateOnBlur={false}
            >
                {({ handleSubmit, setFieldValue, values }) => {
                    let dropzoneParams = {
                        onDropAccepted: (acceptedFiles) => {
                            setFieldValue("files", acceptedFiles);
                        },
                        onDropRejected: (rejectedFiles) => {
                            // TODO: show error message when files are rejected e.g size limit
                            console.error(rejectedFiles[0].errors);
                        },
                        noClick: true,
                        noKeyboard: true,
                        maxSize: maxFileSize,
                        accept: ".jpeg,.jpg,.png"
                    };
                    return (
                        <SemanticForm
                            as={Form}
                            onSubmit={handleSubmit}
                        >
                            <TextField
                                disabled={isUserAuthenticated}
                                label='Name'
                                fieldPath="name"
                                required
                                fluid={false}
                                width={4}
                            />
                            <TextField
                                disabled={isUserAuthenticated}
                                label='Email'
                                fieldPath="email"
                                required
                                fluid={false}
                                width={4}
                            />
                            <CategoryDropdown
                                categories={categories}
                                defaultCategory={defaultCategory}
                            />
                            <TextField
                                label='Subject'
                                fieldPath="subject"
                                required
                                fluid={false}
                                className='mt-10'
                            />
                            <TextAreaField
                                label='Description'
                                fieldPath="description"
                                required
                            />
                            <div className="field">
                                <label>
                                    {`Browser & OS`}
                                </label>
                                <ToggleField
                                    fieldPath='sysInfo'
                                    offLabel='Include browser and system information to assist us with narrowing down the cause of your problem.'
                                    onLabel='Include browser and system information to assist us with narrowing down the cause of your problem.'
                                    offValue={false}
                                    onValue={true}
                                />
                                <label className="helptext">
                                    {sysInfo}
                                </label>
                            </div>
                            <div className="field">
                                <label>
                                    {`Files`}
                                </label>
                                <FileUploader
                                    dropzoneParams={dropzoneParams}
                                    maxFileSize={maxFileSize}
                                    name='files'
                                    currentFiles={values.files}
                                    handleDelete={(file) => {
                                        const newFiles = values.files;
                                        remove(newFiles, file);
                                        setFieldValue("files", newFiles);
                                    }}
                                />
                            </div>
                            <Modal.Actions>
                                <Button type="submit" positive>
                                    Send Request
                                </Button>
                            </Modal.Actions>
                        </SemanticForm>
                    )
                }}
            </Formik>
        );
    }
}


SupportForm.propTypes = {
    userMail: PropTypes.string,
    name: PropTypes.string,
    userBrowser: PropTypes.string,
    userPlatform: PropTypes.string,
    isUserAuthenticated: PropTypes.bool.isRequired,
    categories: PropTypes.array,
    maxFileSize: PropTypes.number,
    descriptionMaxLength: PropTypes.number,
    descriptionMinLength: PropTypes.number,
    apiEndpoint: PropTypes.string.isRequired
};

SubmitEvent.defaultProps = {
    userMail: '',
    name: '',
    userBrowser: '',
    userPlatform: '',
    categories: [],
    maxFileSize: 1000 * 1000 * 10,
    descriptionMaxLength: 5000,
    descriptionMinLength: 20,
}

export default SupportForm;