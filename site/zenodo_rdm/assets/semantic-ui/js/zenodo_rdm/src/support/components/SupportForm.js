import { PropTypes } from "prop-types";
import React, { Component } from "react";
import { Formik, Form } from "formik";
import { Form as SemanticForm, Button, Modal } from "semantic-ui-react";
import { http, TextField, TextAreaField, ToggleField } from "react-invenio-forms";
import { remove } from "lodash/remove";
import { set } from "lodash/set";

import CategoryDropdown from "./CategoryDropdown";
import ReCAPTCHA from "react-google-recaptcha";
import FileUploader from './FileUploader';

// TODO translations
// TODO implement error notification
// TODO required fields are highlighted by the component and not Formik

const requestConfig = {
    headers: {
        "Accept": "application/json",
        'Content-Type': 'multipart/form-data',
    },
};

const ErrorCode = {
    "file-invalid-type": "The file you selected is the wrong format.",
    "file-too-large": "The file you selected is too big. Please add a URL to the file or select a different file.",
    "max-size-exceeded": "Max attachment size exceeded. Please add URLs to the rejected files or make a smaller selection.",
}

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

        this.state = {
            fileErrorMessage: null,
            totalFileSize: 0,
            rejectedFiles: []
        }
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
            maxFileSize,
            recaptchaClientKey
        } = this.props;

        const defaultCategory = categories.length > 0 ? categories[0].key : '';

        const initialValues = {
            email: userMail,
            name: name,
            category: defaultCategory,
            sysInfo: false,
            files: [],
            recaptcha: recaptchaClientKey ? false : true
        }

        const sysInfo = `Browser: ${userBrowser} Operating System: ${userPlatform}`;
        const { fileErrorMessage, rejectedFiles } = this.state;

        return (
            <Formik
                initialValues={initialValues}
                onSubmit={this.onSubmit}
                validateOnChange={false}
                validateOnBlur={false}
            >
                {({ handleSubmit, setFieldValue, values }) => {
                    let dropzoneParams = {
                        validator: (file) => {
                            const { totalFileSize } = this.state;
                            if(totalFileSize + file.size > maxFileSize) {
                                return {code: "max-size-exceeded"}
                            }
                            this.setState({totalFileSize: totalFileSize + file.size});
                        },
                        onDrop: () => {
                            this.setState({ 
                                fileErrorMessage: null,
                                totalFileSize: 0,
                                rejectedFiles: [],
                            });
                        },
                        onDropAccepted: (acceptedFiles) => {
                            setFieldValue("files", acceptedFiles);
                        },
                        onDropRejected: (rejectedFiles) => {
                            const error = rejectedFiles[0].errors[0];
                            rejectedFiles = rejectedFiles.map(file => file.file);

                            this.setState({
                                fileErrorMessage: ErrorCode[error.code],
                                rejectedFiles
                            });
                        },
                        maxSize: maxFileSize,
                        accept: ".jpeg,.jpg,.png",
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
                                width={8}
                                className="field flex"
                            />
                            <TextField
                                disabled={isUserAuthenticated}
                                label='Email'
                                fieldPath="email"
                                required
                                fluid={false}
                                width={8}
                                className="field flex"
                            />
                            <CategoryDropdown
                                categories={categories}
                                defaultCategory={defaultCategory}
                                className="eight wide field flex"
                            />
                            <TextField
                                label='Subject'
                                fieldPath="subject"
                                fluid={false}
                                className='field flex rel-mt-1'
                                required
                            />
                            <TextAreaField
                                label='How can we help?'
                                fieldPath="description"
                                className="field flex"
                                required
                            />

                            <div className="field flex">
                                <label htmlFor="file-dropzone">Files</label>
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
                                    errorMessage={fileErrorMessage}
                                    rejectedFiles={rejectedFiles}
                                />
                            </div>

                            <div className="field flex">
                                <label htmlFor="sysInfo">
                                    Browser & OS
                                </label>
                                <div>
                                    <ToggleField
                                        fieldPath='sysInfo'
                                        offLabel='Include browser and system information to assist us with narrowing down the cause of your problem.'
                                        onLabel='Include browser and system information to assist us with narrowing down the cause of your problem.'
                                        offValue={false}
                                        onValue={true}
                                    />
                                    <label className="helptext">{sysInfo}</label>
                                </div>
                            </div>
                            {
                                recaptchaClientKey &&
                                <div className="field flex">
                                    <ReCAPTCHA
                                        sitekey={recaptchaClientKey}
                                        onChange={(value) => {
                                            setFieldValue('recaptcha', true);
                                        }}
                                    />
                                </div>
                            }
                            <Modal.Actions className="label-padding">
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
    apiEndpoint: PropTypes.string.isRequired,
    recaptchaClientKey: PropTypes.string.isRequired
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