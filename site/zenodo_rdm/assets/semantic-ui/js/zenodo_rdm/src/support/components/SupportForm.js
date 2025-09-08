import { PropTypes } from "prop-types";
import React, { Component } from "react";
import { Formik, Form } from "formik";
import {
  Form as SemanticForm,
  Button,
  Message,
  MessageHeader,
  Modal,
} from "semantic-ui-react";
import { http, TextField, TextAreaField, ToggleField } from "react-invenio-forms";
import _remove from "lodash/remove";
import _set from "lodash/set";

import CategoryDropdown from "./CategoryDropdown";
import FileUploader from "./FileUploader";

// TODO translations
// TODO implement error notification
// TODO implement recaptcha
// TODO required fields are highlighted by the component and not Formik

const requestConfig = {
  headers: {
    "Accept": "application/json",
    "Content-Type": "multipart/form-data",
  },
};

const ErrorCode = {
  "file-invalid-type": "The file you selected is the wrong format.",
  "file-too-large":
    "The file you selected is too big. Please add a URL to the file or select a different file.",
  "max-size-exceeded":
    "Max attachment size exceeded. Please add URLs to the rejected files or make a smaller selection.",
};

function formikToFormData(values) {
  const formData = new FormData();
  // Append each key/value pair to formData
  Object.keys(values).forEach((key) => {
    let currentValue = values[key];
    if (Array.isArray(currentValue)) {
      currentValue.forEach((val) => {
        formData.append(key, val);
      });
    } else {
      formData.append(key, currentValue);
    }
  });

  return formData;
}

class SupportForm extends Component {
  constructor(props) {
    super(props);

    this.state = {
      fileErrorMessage: null,
      totalFileSize: 0,
      rejectedFiles: [],
      loading: false,
      errorStatus: null,
    };
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
          _set(deserializedErrors, e.field, e.messages.join(" "));
        }
      }
    }
    return deserializedErrors;
  };

  onSubmit = async (values, formikBag) => {
    const { apiEndpoint } = this.props;
    this.setState({
      loading: true,
      errorStatus: null,
    });
    try {
      const formData = formikToFormData(values);
      const response = await http.post(apiEndpoint, formData, requestConfig);
      this.setState({ loading: false });
      window.location = response.request.responseURL;
    } catch (error) {
      // API errors need to be deserialised to highlight fields.
      const apiResponse = error?.response?.data;
      if (apiResponse) {
        const apiErrors = apiResponse.errors || [];
        const deserializedErrors = this.deserializeFieldErrors(apiErrors);

        // Highlight errors using formik
        formikBag.setErrors(deserializedErrors);
      }

      this.setState({ errorStatus: error.status });
    }
    this.setState({ loading: false });
  };

  render() {
    const {
      categories,
      name,
      isUserAuthenticated,
      userBrowser,
      userPlatform,
      userMail,
      maxFileSize,
    } = this.props;

    const defaultCategory = categories.length > 0 ? categories[0].key : "";

    const initialValues = {
      email: userMail,
      name: name,
      category: defaultCategory,
      sysInfo: false,
      files: [],
    };

    const sysInfo = `Browser: ${userBrowser} Operating System: ${userPlatform}`;
    const { fileErrorMessage, rejectedFiles, loading, errorStatus } = this.state;

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
              if (totalFileSize + file.size > maxFileSize) {
                return { code: "max-size-exceeded" };
              }
              this.setState({ totalFileSize: totalFileSize + file.size });
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
              rejectedFiles = rejectedFiles.map((file) => file.file);

              this.setState({
                fileErrorMessage: ErrorCode[error.code],
                rejectedFiles,
              });
            },
            maxSize: maxFileSize,
          };
          return (
            <SemanticForm as={Form} onSubmit={handleSubmit}>
              <TextField
                disabled={isUserAuthenticated}
                label="Name"
                fieldPath="name"
                required
                fluid={false}
                width={8}
                className="field flex"
              />
              <TextField
                disabled={isUserAuthenticated}
                label="Email"
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
                label="Subject"
                fieldPath="subject"
                fluid={false}
                className="field flex rel-mt-1"
                required
              />
              <TextAreaField
                label="How can we help?"
                fieldPath="description"
                className="field flex"
                required
              />

              <div className="field flex">
                <label htmlFor="file-dropzone">Files</label>
                <FileUploader
                  dropzoneParams={dropzoneParams}
                  maxFileSize={maxFileSize}
                  name="files"
                  currentFiles={values.files}
                  handleDelete={(file) => {
                    const newFiles = values.files;
                    _remove(newFiles, file);
                    setFieldValue("files", newFiles);
                  }}
                  errorMessage={fileErrorMessage}
                  rejectedFiles={rejectedFiles}
                />
              </div>

              <div className="field flex">
                <label htmlFor="sysInfo">Browser & OS</label>
                <div>
                  <ToggleField
                    fieldPath="sysInfo"
                    offLabel="Include browser and system information to assist us with narrowing down the cause of your problem."
                    onLabel="Include browser and system information to assist us with narrowing down the cause of your problem."
                    offValue={false}
                    onValue
                  />
                  <label className="helptext">{sysInfo}</label>
                </div>
              </div>

              <Modal.Actions className="label-padding">
                <Button type="submit" positive loading={loading} disabled={loading}>
                  Send request
                </Button>
              </Modal.Actions>

              {errorStatus && (
                <Message negative>
                  <MessageHeader>
                    {errorStatus === 400
                      ? "Validation errors"
                      : "Sorry, an error prevented the support ticket from being created"}
                  </MessageHeader>
                  <p>
                    {errorStatus === 400 ? (
                      "Please fix the validation errors indicated above."
                    ) : (
                      <>
                        We kindly ask you to send an email to{" "}
                        <a href="mailto:support@zenodo.org">support@zenodo.org</a> with
                        the same information as in the form above.
                      </>
                    )}
                  </p>
                </Message>
              )}
            </SemanticForm>
          );
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
  apiEndpoint: PropTypes.string.isRequired,
};

SupportForm.defaultProps = {
  userMail: "",
  name: "",
  userBrowser: "",
  userPlatform: "",
  categories: [],
  maxFileSize: 1000 * 1000 * 10,
};

export default SupportForm;
